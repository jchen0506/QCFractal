import * as React from "react";
import { Link, Routes, Route, useLocation, useNavigate, Navigate } from "react-router-dom";
import useAuth from "./useAuth";
import Dashboard from "./Dashboard";
import Login from "./Login";

// const Home = () => <h1>Home (Public)</h1>;
// const Pricing = () => <h1>Pricing (Public)</h1>;

// const Settings = () => <h1>Settings (Private)</h1>;


function Nav() {
	const { authed, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav>
      <ul>
        <li>
          <Link to="/">Home</Link>
        </li>
        <li>
          <Link to="/pricing">Pricing</Link>
        </li>
      </ul>
      {authed && <button onClick={handleLogout}>Logout</button>}
    </nav>
  );
}

function RequireAuth({ children }) {
  const { authed } = useAuth();
  const location = useLocation();

	return authed === true ? (
    children
  ) : (
    <Navigate to="/login" replace state={{ path: location.pathname }} />
  );
}

export default function App() {
  return (
    <div>
			<Routes>			
				<Route
					path="/dashboard"
					element={
						<RequireAuth>
							<Dashboard />
						</RequireAuth>
					}
				/>
				<Route path="/login" element={<Login />} />
			</Routes>
    </div>
  );
}