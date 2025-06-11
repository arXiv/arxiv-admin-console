import React, {useEffect, useState} from "react";
import {Link} from 'react-router-dom';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Button from '@mui/material/Button';
import {useDataProvider} from "react-admin";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

// import { useNavigate } from 'react-router-dom';

interface SummaryProps {
    resource: string;
    title: string;
    filter: object; // { preset: dateRange, _start: null, _end: null }
    link: string;
}


const ResourceSummary: React.FC<SummaryProps> = ({resource, title, filter, link}) => {
    const [count, setCount] = useState<number | string>('Loading...');
    const dataProvider = useDataProvider();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await dataProvider.getList(resource, {
                    filter: filter,
                });
                setCount(response?.total || 0);
            } catch (error) {
                setCount('Error');
                console.error('Error fetching data', error);
            }
        };

        fetchData().then(() => null);
    }, [filter, dataProvider, resource]);

    return (
        <Box sx={{flexGrow: 1, flex: 1}} >
            <Box sx={{ display: 'flex', gap: 2, mb: 1, alignItems: 'center' }}>
            <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1">{title}</Typography>
            </Box>
            <Box sx={{ width: "5em" }}>
                <Link to={link} style={{textDecoration: 'none'}}>
                    <Typography variant="h6">{count}</Typography>
                </Link>
            </Box>
        </Box>
        </Box>
    );
};


interface DateRangeSummaryProps {
    resource: string;
    title: string;
    days: number;
    link: string;
}


const ResourceDateRangeSummary: React.FC<DateRangeSummaryProps> = ({resource, title, days, link}) => {
    const dateRange: string = `last_${days}_days`;
    const filter = {preset: dateRange, _start: null, _end: null};

    return (<ResourceSummary resource={resource} title={title} filter={filter} link={link}/>)
};


export const Dashboard = () => {
    return (
        <Box sx={{ my: 2, display: 'flex', gap: 2 }}>
            <Box sx={{ width: '50%', display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Card>
                    <CardHeader title="Endorsement Request"/>
                    <CardContent sx={{ ml: 2 }}>
                        <ResourceDateRangeSummary
                            resource={"endorsement_requests"} days={1} title={"Today"}
                            link={`/endorsement_requests?displayedFilters={}&filter={"positive"%3Afalse%2C"preset"%3A"1"}&order=DESC&page=1&perPage=25`}/>
                        <ResourceDateRangeSummary
                            resource={"endorsement_requests"} days={7} title={"Last 7 days"}
                            link={`/endorsement_requests?displayedFilters={}&filter={"positive"%3Afalse%2C"preset"%3A"7"}&order=DESC&page=1&perPage=25`}/>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader title="Endorsements"/>
                    <CardContent>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gridTemplateRows: 'repeat(3, 1fr)',
                            height: '100%'
                        }}>
                            <ResourceSummary
                                resource={"endorsements"}
                                title={"Negative"}
                                filter={{positive_endorsement: false}}
                                link={`/endorsements?displayedFilters={}&filter={"positive_endorsement"%3Afalse}&order=DESC&page=1&perPage=2`}
                            />

                            <Box />

                            <ResourceSummary
                                resource={"endorsements"}
                                title={"Today"}
                                filter={{preset: "last_1_days"}}
                                link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_1_days"}&order=DESC&page=1&perPage=2`}
                            />

                            <ResourceSummary
                                resource={"endorsements"}
                                title={"Flagged Today"}
                                filter={{preset: "last_1_days", by_suspect: true}}
                                link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_1_days"%2C"by_suspect"%3Atrue}&order=DESC&page=1&perPage=2`}
                            />

                            <ResourceSummary
                                resource={"endorsements"}
                                title={"Last 7 days"}
                                filter={{preset: "last_7_days"}}
                                link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_7_days"}&order=DESC&page=1&perPage=2`}
                            />

                            <ResourceSummary
                                resource={"endorsements"}
                                title={"Flagged (7 days)"}
                                filter={{preset: "last_7_days", by_suspect: true}}
                                link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_7_days"%2C"by_suspect"%3Atrue}&order=DESC&page=1&perPage=2`}
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader title="Ownership request"/>
                    <CardContent>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gridTemplateRows: 'repeat(3, 1fr)',
                            height: '100%'
                        }}>
                            <ResourceSummary resource={"ownership_requests"} title={"Pending"}
                                             filter={{"workflow_status": "pending"}}
                                             link={`/ownership_requests?displayedFilters={}&filter={"workflow_status"%3A"pending"}&order=ASC&page=1&perPage=25&sort=id`}
                            />
                            <Box />
                            <Typography variant="body1" color="textSecondary" sx={{mt: 1}}>Last week</Typography>
                            <Box />

                            <ResourceSummary
                                resource={"ownership_requests"} title={"Accepted"}
                                filter={{
                                    "workflow_status": "accepted",
                                    "preset": "last_1_days",
                                }}
                                link={`/ownership_requests?displayedFilters={}&filter={"workflow_status"%3A"accepted"%2C"preset"%3A"last_7_days"}&order=ASC&page=1&perPage=25&sort=id`}
                            />
                            <ResourceSummary
                                resource={"ownership_requests"} title={"Rejected"}
                                filter={{
                                    "workflow_status": "rejected",
                                    "preset": "last_7_days"
                                }}
                                link={`/ownership_requests?displayedFilters={}&filter={"workflow_status"%3A"rejected"%2C"preset"%3A"last_7_days"}&order=ASC&page=1&perPage=25&sort=id`}
                            />
                        </div>

                    </CardContent>
                </Card>
            </Box>
            <Box sx={{ width: '50%' }}>
                <Card>
                    <CardHeader title="Users"/>
                    <CardContent>
                        <Box>
                            <Box>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"flag_edit_users":true}'}}>
                                    Administrators
                                </Button>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"flag_is_mod":true}'}}>
                                    Moderators
                                </Button>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"suspect":true}'}}>
                                    Suspect Users
                                </Button>
                            </Box>
                            <Box>
                                <Button component={Link}
                                        to={{pathname: '/users', search: '?filter={"is_non_academic":true}'}}>
                                    Non academic emails for last 90 days
                                </Button>
                            </Box>
                        </Box>
                    </CardContent>
                </Card>
            </Box>
        </Box>
    );
}