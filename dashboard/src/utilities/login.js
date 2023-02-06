import axios from "axios";

function login (username, password) {
	let credential = {
		username: username,
		password: password
	};
	axios.post('https://qcademo.molssi.org/auth/v1/login', credential)
		.then(
			(response) => 
				{
					const token = response.data.access_token;
					const config = {
						headers: { Authorization: `Bearer ${token}` }
					};
				
					axios.get('https://qcademo.molssi.org/api/v1/users/1',config)
						.then(
							(response)=>{
								console.log(response.data)
							}
						)
					// console.log(response.data.access_token);
				}
		)
		.catch(error => {
				console.error('There was an error!', error);
		});
}

login('ben','xOEFGtVpuCkaEXsjQl6Blg');