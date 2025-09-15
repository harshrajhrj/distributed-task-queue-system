import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = 'http://localhost:5000';

function App() {
    const [number, setNumber] = useState('');
    const [tasks, setTasks] = useState([]);

    // This effect will run periodically to check the status of pending tasks
    useEffect(() => {
        const interval = setInterval(() => {
            tasks.forEach(task => {
                if (task.status === 'pending') {
                    fetch(`${API_URL}/task/${task.id}`)
                        .then(res => res.json())
                        .then(data => {
                            if (data.status === 'complete') {
                                setTasks(currentTasks =>
                                    currentTasks.map(t =>
                                        t.id === task.id ? { ...t, status: 'complete', result: data.result } : t
                                    )
                                );
                            }
                        })
                        .catch(console.error);
                }
            });
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(interval);
    }, [tasks]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!number) return;

        const response = await fetch(`${API_URL}/task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ number: parseInt(number) }),
        });

        const data = await response.json();
        setTasks(prevTasks => [...prevTasks, { id: data.task_id, number, status: 'pending', result: null }]);
        setNumber('');
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>Distributed Task Queue</h1>
                <form onSubmit={handleSubmit}>
                    <input
                        type="number"
                        value={number}
                        onChange={(e) => setNumber(e.target.value)}
                        placeholder="Enter a number (e.g., 35)"
                        required
                    />
                    <button type="submit">Calculate Fibonacci</button>
                </form>

                <div className="task-list">
                    <h2>Tasks</h2>
                    {tasks.map((task) => (
                        <div key={task.id} className={`task-item ${task.status}`}>
                            <p><strong>Task ID:</strong> {task.id}</p>
                            <p><strong>Input:</strong> Fibonacci for {task.number}</p>
                            <p><strong>Status:</strong> {task.status}</p>
                            {task.status === 'complete' && <p><strong>Result:</strong> {task.result}</p>}
                        </div>
                    ))}
                </div>
            </header>
        </div>
    );
}

export default App;