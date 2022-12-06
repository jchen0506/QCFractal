import React,  {useEffect} from 'react';
import { Route, Navigate, useLocation } from "@reach/router";

const ProtectedRoute = ({ children, ...rest }) => {
  const location = useLocation();

  useEffect(() => {
    // Check if the user is logged in here...
  }, [location]);

  return (
    <Route
      {...rest}
      render={({ location }) =>
				localStorage.getItem("token") ? (
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
export default ProtectedRoute;