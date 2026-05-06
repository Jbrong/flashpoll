import { useState, useEffect } from 'react';


function VotePoll({ pollId }) {
    const [poll, setPoll] = useState(null);
    const [voted, setVoted] = useState(false);
    useEffect(() => {
        fetch(`http://localhost:8080/api/polls/${pollId}`)
            .then((response) => response.json())
            .then((data) => setPoll(data))
            }, [pollId]);

    return (
        <div>
            <h2>Vote on a Poll</h2>
            {poll ? <h3>{poll.poll_question}</h3> : <p>Loading...</p>}

            {poll && poll.poll_answer_options.map((option) => (
                  <button
                      key={option}
                      onClick={() => {
                          fetch(`http://localhost:8080/api/polls/${pollId}/vote`, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ poll_answer_option: option })
                          })
                              .then(setVoted(true));
                      }}
                  >
                      {option}
                  </button>
            ))}
            {voted && <p>Thank you for voting!</p>}

            <pre>{JSON.stringify(poll, null, 2)}</pre>
        </div>
    )
}

export default VotePoll;