import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

function InfoCard() {
	const [name, setName] = useState(null);
	const [version, setVersion] = useState(null);

	useEffect(()=>{
		fetch('https://api.qcarchive.molssi.org/api/v1/information')
			.then( response => response.json())
      .then((info) => { 
				setName(info.name);
				setVersion(info.version)
			})
			.catch(err => console.log(err));
	},[])

	return (
		<Card sx={{ minWidth: 100 }}>
		<CardContent>
			<Typography sx={{ fontSize: 20, fontWeight: 700 }}  component="div">
				{ name }
			</Typography>
			<Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
				Version: { version }
			</Typography>
		</CardContent>
		<CardActions>
			<Button size="small">Learn More</Button>
		</CardActions>
	</Card>
	)

}

export default InfoCard;