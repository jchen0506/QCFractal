import React, { useState, useEffect } from 'react';
import {
  Router,
  Route,
  Navigate,
  Routes,
  useLocation
} from '@reach/router';

const AdminDashboard = () => {
  return (
    <div>
      <h1>Admin Dashboard</h1>
      <p>Welcome to the admin dashboard!</p>
    </div>
  );
};

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = event => {
    event.preventDefault();

    // Perform login logic here...

    setIsLoggedIn(true);
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <label>
          Username:
          <input
            type="text"
            value={username}
            onChange={event => setUsername(event.target.value)}
          />
        </label>
        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={event => setPassword(event.target.value)}
          />
        </label>
        <button type="submit">Login</button>
      </form>
    </div>
  );
};

const PrivateRoute = ({ children, ...rest }) => {
  const location = useLocation();

  useEffect(() => {
    // Check if the user is logged in here...
  }, [location]);

  return (
    <Route
      {...rest}
      render={({ location }) =>
        isLoggedIn ? (
          children
        ) : (
          <Navigate
            to={{
              pathname: '/login',
              state: { from: location }
            }}
          />
        )
      }
    />
  );
};

const App = () => {
  return (
    <Router>
      <Routes>
        <PrivateRoute exact path="/admin">
          <AdminDashboard />
        </PrivateRoute>
        <Route exact path="/login" component={LoginPage} />
      </Routes>
    </Router>
  );
};
