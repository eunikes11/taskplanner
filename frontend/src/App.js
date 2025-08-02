import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user_id, username: userName } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser({ user_id, username: userName });
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { username, password });
      const { access_token, user_id, username: userName } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser({ user_id, username: userName });
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, token }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin ? await login(username, password) : await register(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-blue-400 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🌟 My Task Planner
          </h1>
          <p className="text-gray-600">Plan your awesome day!</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 text-lg"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 text-lg"
              placeholder="Enter your password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold py-3 px-4 rounded-xl hover:from-purple-600 hover:to-pink-600 transition duration-300 transform hover:scale-105 disabled:opacity-50 text-lg"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>

        <div className="text-center mt-6">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-purple-600 hover:text-purple-800 font-medium"
          >
            {isLogin ? "Don't have an account? Sign up!" : "Already have an account? Login!"}
          </button>
        </div>
      </div>
    </div>
  );
};

// Task Management Component
const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [stats, setStats] = useState({ total_tasks: 0, completed_tasks: 0, remaining_tasks: 0 });
  const [showMotivation, setShowMotivation] = useState(false);
  const [draggedTask, setDraggedTask] = useState(null);
  const { user, logout, token } = useAuth();

  const api = axios.create({
    headers: { Authorization: `Bearer ${token}` }
  });

  useEffect(() => {
    fetchTasks();
    fetchStats();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await api.get(`${API}/tasks`);
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get(`${API}/tasks/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const addTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
      await api.post(`${API}/tasks`, { title: newTaskTitle.trim() });
      setNewTaskTitle('');
      fetchTasks();
      fetchStats();
    } catch (error) {
      console.error('Error adding task:', error);
    }
  };

  const toggleTask = async (taskId, completed) => {
    try {
      await api.put(`${API}/tasks/${taskId}`, { completed });
      fetchTasks();
      fetchStats();
      
      // Check if all tasks are completed
      const updatedTasks = tasks.map(task => 
        task.id === taskId ? { ...task, completed } : task
      );
      const allCompleted = updatedTasks.every(task => task.completed) && updatedTasks.length > 0;
      
      if (allCompleted && completed) {
        setShowMotivation(true);
        setTimeout(() => setShowMotivation(false), 5000);
      }
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await api.delete(`${API}/tasks/${taskId}`);
      fetchTasks();
      fetchStats();
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  const handleDragStart = (e, task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, targetTask) => {
    e.preventDefault();
    
    if (!draggedTask || draggedTask.id === targetTask.id) return;

    const newTasks = [...tasks];
    const draggedIndex = newTasks.findIndex(t => t.id === draggedTask.id);
    const targetIndex = newTasks.findIndex(t => t.id === targetTask.id);

    // Remove dragged task and insert at target position
    newTasks.splice(draggedIndex, 1);
    newTasks.splice(targetIndex, 0, draggedTask);

    // Update order_index for all tasks
    const taskOrders = newTasks.map((task, index) => ({
      id: task.id,
      order_index: index
    }));

    try {
      await api.post(`${API}/tasks/reorder`, { task_orders: taskOrders });
      fetchTasks();
    } catch (error) {
      console.error('Error reordering tasks:', error);
    }

    setDraggedTask(null);
  };

  const generatePDF = () => {
    // Create a simple printable version
    const printContent = `
      <html>
        <head>
          <title>My Daily Task Plan</title>
          <style>
            body { font-family: 'Comic Sans MS', cursive; padding: 20px; }
            h1 { color: #8B5CF6; text-align: center; }
            .task { margin: 10px 0; padding: 10px; border: 2px solid #E5E7EB; border-radius: 10px; }
            .task-number { font-weight: bold; color: #8B5CF6; }
          </style>
        </head>
        <body>
          <h1>🌟 My Awesome Task Plan for Today! 🌟</h1>
          <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
          <p><strong>Planner:</strong> ${user.username}</p>
          <hr>
          ${tasks.filter(task => !task.completed).map((task, index) => `
            <div class="task">
              <span class="task-number">${index + 1}.</span> ${task.title}
              <div style="margin-top: 10px;">
                ☐ Done!
              </div>
            </div>
          `).join('')}
          <hr>
          <p style="text-align: center; color: #8B5CF6; font-weight: bold;">
            You've got this! Every task you finish makes you stronger! 💪✨
          </p>
        </body>
      </html>
    `;

    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-purple-50 to-pink-100">
      {/* Header */}
      <div className="bg-white shadow-lg border-b-4 border-purple-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-gray-800">
                🌟 Hey {user.username}!
              </h1>
              <p className="text-gray-600 text-lg">What awesome things will you do today?</p>
            </div>
            <button
              onClick={logout}
              className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-xl transition duration-300"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="stats-card stats-card-total">
            <div className="text-3xl font-bold text-white">{stats.total_tasks}</div>
            <div className="text-purple-100">Total Tasks</div>
          </div>
          <div className="stats-card stats-card-completed">
            <div className="text-3xl font-bold text-white">{stats.completed_tasks}</div>
            <div className="text-green-100">Completed</div>
          </div>
          <div className="stats-card stats-card-remaining">
            <div className="text-3xl font-bold text-white">{stats.remaining_tasks}</div>
            <div className="text-orange-100">Remaining</div>
          </div>
        </div>

        {/* Add Task Form */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <form onSubmit={addTask} className="space-y-4">
            <div>
              <label className="block text-2xl font-bold text-gray-800 mb-3">
                What do you want to do today? ✨
              </label>
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                className="w-full px-4 py-4 text-lg border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Type your awesome task here..."
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold py-4 px-6 rounded-xl hover:from-purple-600 hover:to-pink-600 transition duration-300 transform hover:scale-105 text-lg"
            >
              Add Task 🚀
            </button>
          </form>
        </div>

        {/* Action Buttons */}
        {tasks.length > 0 && (
          <div className="flex flex-wrap gap-4 mb-8">
            <button
              onClick={generatePDF}
              className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-xl transition duration-300 transform hover:scale-105"
            >
              🖨️ Print My Plan
            </button>
          </div>
        )}

        {/* Tasks List */}
        <div className="space-y-4">
          {tasks.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎯</div>
              <p className="text-2xl text-gray-600 font-bold">Ready to plan your amazing day?</p>
              <p className="text-lg text-gray-500">Add your first task above!</p>
            </div>
          ) : (
            tasks.map((task, index) => (
              <div
                key={task.id}
                draggable
                onDragStart={(e) => handleDragStart(e, task)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, task)}
                className={`task-card ${task.completed ? 'task-completed' : ''} cursor-move`}
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="task-number">{index + 1}</div>
                  </div>
                  
                  <div className="flex-grow">
                    <div className={`text-lg font-medium ${task.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}>
                      {task.title}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleTask(task.id, !task.completed)}
                      className={`task-checkbox ${task.completed ? 'task-checkbox-completed' : ''}`}
                    >
                      {task.completed && <span className="checkmark">✓</span>}
                    </button>
                    
                    <button
                      onClick={() => deleteTask(task.id)}
                      className="text-red-500 hover:text-red-700 text-xl p-1"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Motivational Message */}
        {showMotivation && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-3xl p-8 mx-4 max-w-md text-center animate-bounce">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-3xl font-bold text-purple-600 mb-4">Amazing Work!</h2>
              <p className="text-lg text-gray-700 mb-6">
                Great job today! Every task you finish makes you stronger and smarter. 
                Get ready to rock tomorrow too! 💪🌟
              </p>
              <button
                onClick={() => setShowMotivation(false)}
                className="bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold py-3 px-6 rounded-xl hover:from-purple-600 hover:to-pink-600 transition duration-300"
              >
                Awesome! 🚀
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <AuthenticatedApp />
      </div>
    </AuthProvider>
  );
}

const AuthenticatedApp = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-blue-400 flex items-center justify-center">
        <div className="text-white text-2xl font-bold">Loading your awesome planner... 🌟</div>
      </div>
    );
  }

  return user ? <TaskManager /> : <LoginForm />;
};

export default App;