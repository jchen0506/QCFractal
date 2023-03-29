import * as React from "react";
import { useCookies } from "react-cookie";

const authContext = React.createContext();

function useAuth() {
	const [authed, setAuthed] = React.useState(false);
	const [cookies, setCookie] = useCookies(['access_token', 'refresh_token'])

	return {
		authed,
		async login(credentials) {
			try {
				const response = await fetch('https://validation.qcarchive.molssi.org/auth/v1/login', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify({
						username: credentials.username,
						password: credentials.password,
					}),
				});
				const responseJson = await response.json();
				console.log(responseJson);

				if (response.status === 200) {

					setCookie('access_token', responseJson.access_token, { path: '/', expires: new Date(Date.now() + 604800000) },);

					setCookie('refresh_token', responseJson.refresh_token, { path: '/', expires: new Date(Date.now() + 604800000) },);

					return new Promise((res) => {
						setAuthed(true);
						res();
					});
				}
			} catch (error) {
				console.error(error);
			}
		},
		logout() {
			return new Promise((res) => {
				setAuthed(false);
				res();
			});
		},
	};
}

export function AuthProvider({ children }) {
	const auth = useAuth();

	return <authContext.Provider value={auth}>{children}</authContext.Provider>;
}

export default function AuthConsumer() {
	return React.useContext(authContext);
}