import * as React from "react";
import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import useAuth from "./useAuth";
import Dashboard from "./Dashboard";
// import Login from "./Login";
import SignIn from "./SignIn";
// const Home = () => <h1>Home (Public)</h1>;
// const Pricing = () => <h1>Pricing (Public)</h1>;

// const Settings = () => <h1>Settings (Private)</h1>;



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
					<Route
						path="/"
						element={
							<RequireAuth>
								<Dashboard />
							</RequireAuth>
						}
					/>
					<Route path="/login" element={<SignIn />} />
				</Routes>
			</div>
	);
}