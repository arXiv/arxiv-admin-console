import React, {useEffect, useState} from "react";
import { Link } from 'react-router-dom';
import {Card, CardContent, CardHeader, Grid, Button} from '@mui/material';
import {useDataProvider} from "react-admin";
import Typography from "@mui/material/Typography";
// import { useNavigate } from 'react-router-dom';

interface SummaryProps {
    resource: string;
    title: string;
    filter: object; // { preset: dateRange, _start: null, _end: null }
    link: string;
}

const ResourceSummary: React.FC<SummaryProps> = ({ resource, title, filter, link }) => {
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

        fetchData().then(_ => null);
    }, [filter, dataProvider, resource]);

    return (
        <Grid container item xs={12}>
            <Grid item xs={3}>
                <Typography variant="subtitle1">{title}</Typography>
            </Grid>
            <Link to={link}>
                <Grid item xs={3}>
                    <Typography variant="h6">{count}</Typography>
                </Grid>
            </Link>
        </Grid>
    );
};


interface DateRangeSummaryProps {
    resource: string;
    title: string;
    days: number;
    link: string;
}


const ResourceDateRangeSummary: React.FC<DateRangeSummaryProps> = ({ resource, title, days, link }) => {
    const dateRange: string = `last_${days}_days`;
    const filter = { preset: dateRange, _start: null, _end: null };

    return (<ResourceSummary resource={resource} title={title} filter={filter} link={link} />)
};


export const Dashboard = () => {
    return (
        <Grid container>
            <Grid item xs={5}>
        <Card>
            <CardHeader title="Submission status" />
            <CardContent>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Grid item container xs={12}>
                            <Typography variant="body1" color="textSecondary">Endorsement Request Summary</Typography>
                            <Grid item container xs={12}>
                                <ResourceDateRangeSummary
                                    resource={"endorsement_requests"} days={1} title={"Today"}
                                                 link={`/endorsement_requests?displayedFilters={}&filter={"not_positive"%3Atrue%2C"preset"%3A"1"}&order=DESC&page=1&perPage=25`}/>
                                <ResourceDateRangeSummary
                                    resource={"endorsement_requests"} days={7} title={"Last 7 days"}
                                                 link={`/endorsement_requests?displayedFilters={}&filter={"not_positive"%3Atrue%2C"preset"%3A"7"}&order=DESC&page=1&perPage=25`}/>
                                <ResourceDateRangeSummary
                                    resource={"endorsement_requests"} days={30} title={"Last 30 days"}
                                                 link={`/endorsement_requests?displayedFilters={}&filter={"not_positive"%3Atrue%2C"preset"%3A"60"}&order=DESC&page=1&perPage=25`}/>
                            </Grid>
                        </Grid>

                        <Grid item container xs={12}>
                            <Typography variant="body1" color="textSecondary">Endorsement Summary</Typography>
                            <Grid item container xs={12}>
                                <ResourceDateRangeSummary
                                    resource={"endorsements"} days={1} title={"Today"}
                                                 link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_1_days"}&order=DESC&page=1&perPage=25`}
                                />
                                <ResourceDateRangeSummary
                                    resource={"endorsements"} days={7} title={"Last 7 days"}
                                                 link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_7_days"}&order=DESC&page=1&perPage=25`}
                                />
                                <ResourceDateRangeSummary
                                    resource={"endorsements"} days={30} title={"Last 30 days"}
                                                 link={`/endorsements?displayedFilters={}&filter={"preset"%3A"last_30_days"}&order=DESC&page=1&perPage=25`}
                                />
                            </Grid>
                        </Grid>

                        <Grid item container xs={12}>
                            <Typography variant="body1" color="textSecondary">Ownership request Summary</Typography>
                            <Grid item container xs={12}>
                                <ResourceSummary resource={"ownership_requests"} title={"Pending"}
                                                 filter={{"workflow_status": "pending"}}
                                                 link={`/ownership_requests?displayedFilters={}&filter={"workflow_status"%3A"pending"}&order=ASC&page=1&perPage=25&sort=id`}
                                />
                            </Grid>
                            <Grid item container xs={12}>
                                <Grid item container xs={1} />
                                <Grid item container xs={11}>
                                    <Typography variant="body1" color="textSecondary">Last week</Typography>

                                    <ResourceSummary resource={"ownership_requests"} title={"Accepted"}
                                                     filter={{"workflow_status": "accepted", "preset": "last_7_days"}}
                                                     link={`/ownership_requests?displayedFilters={}&filter={"workflow_status"%3A"accepted"%2C"preset"%3A"last_7_days"}&order=ASC&page=1&perPage=25&sort=id`}
                                    />
                                    <ResourceSummary resource={"ownership_requests"} title={"Rejected"}
                                                     filter={{"workflow_status": "rejected", "preset": "last_7_days"}}
                                                     link={`/ownership_requests?displayedFilters={}&filter={"workflow_status"%3A"rejected"%2C"preset"%3A"last_7_days"}&order=ASC&page=1&perPage=25&sort=id`}
                                    />
                                </Grid>
                            </Grid>

                        </Grid>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
        </Grid>
            <Grid item xs={5}>
                <Card>
                    <CardHeader title="Users" />
                    <CardContent>
                        <Grid container spacing={2}>
                            <Grid item xs={12}>
                                <Grid item container xs={12}>
                                    <Button component={Link} to={{ pathname: '/users', search: '?filter={"flag_edit_users":true}' }}>
                                        Administrators
                                    </Button>
                                    <Button component={Link} to={{ pathname: '/users', search: '?filter={"flag_is_mod":true}' }}>
                                        Moderators
                                    </Button>
                                    <Button component={Link} to={{ pathname: '/users', search: '?filter={"suspect":true}' }}>
                                        Suspect Users
                                    </Button>
                                </Grid>
                                <Grid item container xs={12}>
                                    <Button component={Link} to={{ pathname: '/users', search: '?filter={"is_non_academic":true}' }}>
                                        Non academic emails for last 90 days
                                    </Button>
                                </Grid>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            </Grid>

        </Grid>
    );
}
