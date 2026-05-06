import CreatePoll from './pages/CreatePoll';
import VotePoll from './pages/VotePoll';

function App() {
  return (
      <div>
        <h1>FlashPoll</h1>
          <CreatePoll />
          <VotePoll pollId="a4cc7835-e015-45fc-bcb7-90bb87a95c6f" />
      </div>
  );
}

export default App;
