import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

class InfoCard extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			name: null,
			version: null,
		}
	}

	componentDidMount() {
    fetch('https://api.qcarchive.molssi.org/api/v1/information')
			.then( response => response.json())
      .then((info) => { 
				console.log(info);
				this.setState({
				name: info.name,
				version: info.version
			})})
			.catch(err => console.log(err));
  }

	render() {
		return (
			<Card sx={{ minWidth: 100 }}>
      <CardContent>
        <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
          Name: {this.state.name}
        </Typography>
        <Typography variant="h5" component="div">
          Version {this.state.version}
        </Typography>
      </CardContent>
      <CardActions>
        <Button size="small">Learn More</Button>
      </CardActions>
    </Card>
		)
	}
}

export default InfoCard;