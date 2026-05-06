import { useState } from 'react';

function CreatePoll() {
    const [question, setQuestion] = useState('');
    const [options, setOptions] = useState(['','']);
    const [pollId, setPollId] = useState(null);

    return (
        <div>
            <h2>Create a Poll</h2>
            <input type="text"
                   placeholder="Enter your question"
                   value={question}
                   onChange={(e) => setQuestion(e.target.value)}
            />
            {options.map((option, index) => (
                <input
                key={index}
                type="text"
                placeholder={`Option ${index + 1}`}
                value={option}
                onChange={(e) => {
                    const newOptions = [...options];
                    newOptions[index] = e.target.value;
                    setOptions(newOptions);
                }}
                />
            ))}
            <button onClick={() => setOptions([...options, ''])}>Add Option</button>
            <button onClick={() => {
                fetch('http://localhost:8080/api/polls', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        poll_question: question,
                        poll_answer_options: options,
                        poll_vote_control: "one_per_ip",
                        poll_results_visibility: "live",
                        poll_expiry: 15
                    })
                })
                    .then((response) => response.json())
                    .then((data) => {
                        setPollId(data.poll_id);
                        console.log(data);
                    });
            }}>Create</button>
            {pollId && <p>Poll ID: {pollId}</p>}
        </div>
    );
}

export default CreatePoll;