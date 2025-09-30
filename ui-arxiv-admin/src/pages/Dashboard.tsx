import React, {useContext, useEffect, useState} from "react";
import {Link} from 'react-router-dom';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Button from '@mui/material/Button';
import {useDataProvider} from "react-admin";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import { BoxProps } from '@mui/material/Box';
import { RuntimeContext } from "../RuntimeContext";
import Paper from "@mui/material/Paper";
import NavCard from '../bits/NavCard';

// import { useNavigate } from 'react-router-dom';

interface SummaryProps extends Omit<BoxProps, 'title'> {
    resource: string;
    title: string;
    filter: object; // { preset: dateRange, _start: null, _end: null }
    link: string;
}


const ResourceSummary: React.FC<SummaryProps> = ({
    resource,
    title,
    filter,
    link,
    sx,
    ...boxProps // rest of Box props
}) => {
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
        <Box 
            sx={{ 
                flexGrow: 1, 
                flex: 1,
                ...sx 
            }}
            {...boxProps}
        >
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
    const runtimeProps = useContext(RuntimeContext);

    return (
        <Box
            sx={{
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                p: 3,
                mt: 3
            }}
        >
            <Box
                sx={{
                    width: { xs: '100%', sm: '80%' },
                    maxWidth: '1200px'
                }}
            >
                <Typography fontSize={"3rem"} fontWeight={700} component={"h1"}>Welcome {runtimeProps.currentUser?.first_name}</Typography>
                <Box sx={{ my: 2, display: 'flex', gap: 2, mt: 4 }}>
                    <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2, width: '100%' }}>
                        {runtimeProps.arxivNavLinks.map(navSection => (
                            <Box key={navSection.id} sx={{ flex: 1 }}>
                                <NavCard navSection={navSection} />
                            </Box>
                        ))}
                    </Box>
                </Box>
            </Box>
        </Box>
    );
}