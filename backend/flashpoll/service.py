"""Poll rules: lifecycle, vote control and results visibility (docs/spec.md, section 1)."""

from . import clock
from .config import Settings
from .errors import AlreadyVoted, ApiError, PollClosed, PollNotFound, ResultsHidden, Unauthorized
from .models import (
    AdminPollView,
    CreatePollRequest,
    CreatePollResponse,
    PollStatus,
    PollView,
    Results,
    ResultsResponse,
    ResultsVisibility,
    VoteControl,
)
from .security import hash_admin_token, new_admin_token, new_poll_id, voter_key
from .store import PollIdTaken, PollStore, VoteRejected

GRACE_PERIOD_SECONDS = 24 * 60 * 60
CREATE_ATTEMPTS = 5


class PollService:
    def __init__(self, store: PollStore, settings: Settings):
        self.store = store
        self.settings = settings

    # --- create -----------------------------------------------------------

    def create_poll(self, request: CreatePollRequest) -> CreatePollResponse:
        now = clock.now()
        expires_at = now + request.expires_in_minutes * 60
        admin_token = new_admin_token()
        poll = {
            "admin_token_hash": hash_admin_token(admin_token),
            "question": request.question,
            "options": request.options,
            "vote_control": request.vote_control.value,
            "results_visibility": request.results_visibility.value,
            "counts": {str(i): 0 for i in range(len(request.options))},
            "total_votes": 0,
            "created_at": now,
            "expires_at": expires_at,
            "ttl": expires_at + GRACE_PERIOD_SECONDS,
        }
        for _ in range(CREATE_ATTEMPTS):
            poll["poll_id"] = new_poll_id()
            try:
                self.store.create_poll(poll)
                break
            except PollIdTaken:
                continue
        else:
            raise RuntimeError("Could not allocate a unique poll id")

        return CreatePollResponse(
            poll_id=poll["poll_id"],
            admin_token=admin_token,
            share_url=f"{self.settings.app_url}/p/{poll['poll_id']}",
            admin_url=f"{self.settings.app_url}/admin#{admin_token}",
            expires_at=clock.iso(expires_at),
        )

    # --- public reads -----------------------------------------------------

    def get_poll(self, poll_id: str, voter_token: str | None) -> PollView:
        poll = self._load(poll_id)
        has_voted = self._has_voted(poll, voter_token)
        return self._view(poll, has_voted)

    def get_results(self, poll_id: str, voter_token: str | None) -> ResultsResponse:
        poll = self._load(poll_id)
        if not self._results_visible(poll, self._has_voted(poll, voter_token)):
            raise ResultsHidden()
        return ResultsResponse(status=_status(poll), **_results(poll).model_dump())

    # --- voting -----------------------------------------------------------

    def vote(
        self, poll_id: str, option_index: int, voter_token: str | None, ip: str
    ) -> Results | None:
        poll = self._load(poll_id)
        if _status(poll) is PollStatus.closed:
            raise PollClosed()
        if option_index >= len(poll["options"]):
            raise ApiError(422, "invalid_request", "option_index is out of range")

        control = VoteControl(poll["vote_control"])
        if control is VoteControl.one_per_browser and not voter_token:
            raise ApiError(422, "invalid_request", "X-Voter-Token header is required for this poll")

        markers: list[tuple[str, bool]] = []
        if control is VoteControl.one_per_ip:
            markers.append((voter_key("ip", poll_id, ip), True))
        if voter_token:
            markers.append(
                (voter_key("vt", poll_id, voter_token), control is VoteControl.one_per_browser)
            )

        try:
            self.store.record_vote(poll, option_index, clock.now(), markers)
        except VoteRejected as rejected:
            if not rejected.poll_rejected:
                raise AlreadyVoted() from None
            if self.store.get_poll(poll_id) is None:
                raise PollNotFound() from None
            raise PollClosed() from None

        poll = self._load(poll_id)
        if not self._results_visible(poll, has_voted=voter_token is not None):
            return None
        return _results(poll)

    # --- admin ------------------------------------------------------------

    def admin_view(self, admin_token: str | None) -> AdminPollView:
        return self._admin_view(self._load_admin(admin_token))

    def admin_close(self, admin_token: str | None) -> AdminPollView:
        poll = self._load_admin(admin_token)
        self.store.close_poll(poll["poll_id"], clock.now())
        return self._admin_view(self._load(poll["poll_id"]))

    def admin_delete(self, admin_token: str | None) -> None:
        poll = self._load_admin(admin_token)
        self.store.delete_poll(poll["poll_id"])

    # --- helpers ----------------------------------------------------------

    def _load(self, poll_id: str) -> dict:
        poll = self.store.get_poll(poll_id)
        # TTL deletion can lag, so anything past its ttl is treated as already gone.
        if poll is None or poll["ttl"] <= clock.now():
            raise PollNotFound()
        return poll

    def _load_admin(self, admin_token: str | None) -> dict:
        if not admin_token:
            raise Unauthorized()
        poll = self.store.find_by_admin_hash(hash_admin_token(admin_token))
        if poll is None:
            raise Unauthorized()
        # Re-read from the base table: the index is eventually consistent.
        return self._load(poll["poll_id"])

    def _has_voted(self, poll: dict, voter_token: str | None) -> bool:
        if not voter_token:
            return False
        return self.store.has_voter(poll["poll_id"], voter_key("vt", poll["poll_id"], voter_token))

    def _results_visible(self, poll: dict, has_voted: bool) -> bool:
        visibility = ResultsVisibility(poll["results_visibility"])
        if visibility is ResultsVisibility.live:
            return True
        if visibility is ResultsVisibility.after_voting:
            return has_voted or _status(poll) is PollStatus.closed
        return False

    def _view(self, poll: dict, has_voted: bool) -> PollView:
        return PollView(
            poll_id=poll["poll_id"],
            question=poll["question"],
            options=poll["options"],
            vote_control=poll["vote_control"],
            results_visibility=poll["results_visibility"],
            created_at=clock.iso(poll["created_at"]),
            expires_at=clock.iso(poll["expires_at"]),
            status=_status(poll),
            has_voted=has_voted,
            results_available=self._results_visible(poll, has_voted),
        )

    def _admin_view(self, poll: dict) -> AdminPollView:
        return AdminPollView(
            **self._view(poll, has_voted=False).model_dump(),
            results=_results(poll),
            deletes_at=clock.iso(poll["ttl"]),
        )


def _status(poll: dict) -> PollStatus:
    return PollStatus.open if poll["expires_at"] > clock.now() else PollStatus.closed


def _results(poll: dict) -> Results:
    counts = [poll["counts"].get(str(i), 0) for i in range(len(poll["options"]))]
    return Results(total_votes=poll["total_votes"], counts=counts)
