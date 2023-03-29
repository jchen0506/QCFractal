import React, { useState, useEffect } from 'react';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useCookies } from 'react-cookie';

function InfoCard() {
	const [name, setName] = useState(null);
	const [version, setVersion] = useState(null);
	const [cookies, setCookie] = useCookies(['access_token', 'refresh_token'])


	const accessToken = cookies.access_token;
	const refreshToken = cookies.refresh_token;
	useEffect(() => {

		fetch('https://validation.qcarchive.molssi.org/api/v1/information', {
			headers: {
				Authorization: `Bearer ${accessToken}`
			}
		})
			.then(response => response.json())
			.then((info) => {
				console.log(info)
				setName(info.name);
				setVersion(info.version)
			})
			.catch(err => console.log(err));
	}, [])

	return (
		<Card sx={{ minWidth: 100 }}>
			<CardContent>
				<Typography sx={{ fontSize: 20, fontWeight: 700 }} component="div">
					{name}
				</Typography>
				<Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
					Version: {version}
				</Typography>
			</CardContent>
			<CardActions>
				<Button size="small">Learn More</Button>
			</CardActions>
		</Card>
	)

}

export default InfoCard;