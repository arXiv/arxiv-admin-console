import React from 'react';
import {
    AppBar as RaAppBar,
    useDataProvider,
} from 'react-admin';
import TextField from '@mui/material/TextField';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {PanelToggleButton} from "../components/PanelToggleButton";
import {useTheme} from "@mui/material/styles";
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import {ArxivUserMenu} from "../components/ArxivUserMenu";
import Button from '@mui/material/Button';
import LaunchIcon from '@mui/icons-material/Launch';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import {RuntimeContext} from "../RuntimeContext";
import {ArxivNavLink} from "../arxivNavLinks";
import ArxivNavMenu from './ArxivNavMenu';
import {useMediaQuery} from "@mui/material";

export const AdminConsoleAppBar = () => {
    const runtimeProps = React.useContext(RuntimeContext);
    const [userSearch, setUserSearch] = useState('');
    const [docSearch, setDocSearch] = useState('');
    const [anchorEls, setAnchorEls] = useState<{ [key: string]: HTMLElement | null }>({});
    const navigate = useNavigate();
    const dataProvider = useDataProvider();
    const theme = useTheme();
    // const isDark = theme.palette.mode === 'dark';
    const isVerySmall = useMediaQuery<any>(theme => theme.breakpoints.down('md'));

    const handleUserSearch = (e: React.KeyboardEvent) => {
        let criteria = {}
        const searchTerm = userSearch.trim().replace(/\s+/g, ' '); // Remove extra spaces/tabs

        if (e.key === 'Enter' && searchTerm) {
            if (searchTerm.endsWith('@')) {
                criteria = {username: searchTerm.substring(0, searchTerm.length - 1)}
            } else if (searchTerm.includes('@')) {
                criteria = {email: searchTerm}
            } else {
                let terms = searchTerm.split(" ");

                // Handle comma-separated format (last, first)
                if (searchTerm.includes(',')) {
                    const commaSplit = searchTerm.split(',');
                    if (commaSplit.length === 2) {
                        const lastName = commaSplit[0].trim();
                        const firstName = commaSplit[1].trim();
                        criteria = {first_name: firstName, last_name: lastName};
                    } else {
                        // If multiple commas or malformed, treat as single last name
                        criteria = {last_name: searchTerm.replace(/,/g, '').trim()};
                    }
                } else {
                    // Normal space-separated format
                    criteria = (terms.length > 1) ? {first_name: terms[0], last_name: terms[1]} : {last_name: terms[0]}
                }
            }
            const filter = encodeURIComponent(JSON.stringify(criteria));
            navigate(`/users?filter=${filter}`);
        }
    };

    const handleDocSearch = async (e: React.KeyboardEvent) => {
        const searchTerm = docSearch.trim();
        if (e.key === 'Enter' && searchTerm) {
            if (searchTerm.startsWith('s/')) {
                const criteria = searchTerm.substring(2);
                const isAllDigits = /^\d+$/.test(criteria);
                if (isAllDigits) {
                    navigate(`/submissions/${criteria}`);
                } else {
                    const destination = `/submissions?displayedFilters=%7B"title"%3Atrue%7D&filter=%7B"title"%3A"${encodeURIComponent(criteria)}"%7D&order=DESC&page=1&perPage=10&sort=id`;
                    navigate(destination);
                }
            } else if (searchTerm.startsWith('d/')) {
                const criteria = searchTerm.substring(2);
                const isAllDigits = /^\d+$/.test(criteria);
                if (isAllDigits) {
                    navigate(`/documents/${criteria}/show`);
                } else {
                    const destination = `/documents?displayedFilters=%7B"title"%3Atrue%7D&filter=%7B"title"%3A"${encodeURIComponent(criteria)}"%7D&order=DESC&page=1&perPage=10&sort=id`;
                    navigate(destination);
                }
            } else if (searchTerm.includes('/') || searchTerm.includes('.')) {
                console.log("doc search: " + searchTerm);
                try {
                    const {data} = await dataProvider.getList('documents', {
                        pagination: {page: 1, perPage: 100},
                        sort: {field: 'id', order: 'ASC'},
                        filter: {paper_id: searchTerm},
                    });

                    if (data.length === 1) {
                        // Navigate to /documents/:id
                        const documentId = data[0].id;
                        console.log(JSON.stringify(data));
                        const url = `/documents/${documentId}/show`;
                        navigate(url);
                    } else {
                        // No match: go to filtered list
                        const filter = encodeURIComponent(JSON.stringify({paper_id: searchTerm}));
                        const url = `/documents?filter=${filter}&sort=id&order=ASC&page=1`;
                        console.log(url);
                        navigate(url);
                    }
                } catch (err) {
                    const filter = encodeURIComponent(JSON.stringify({paper_id: searchTerm}));
                    const url = `/documents?filter=${filter}&sort=id&order=ASC&page=1`;
                    console.log(err);
                    console.log(url);
                    navigate(url);
                }
            } else {
                const criteria = {id: searchTerm}
                const filter = encodeURIComponent(JSON.stringify(criteria));
                // navigate(`/submissions?filter=${filter}}`);
                navigate(`/submissions/${searchTerm}/show`);
            }
        }
    };

    return (
        <RaAppBar sx={{zIndex: 1300}} userMenu={<ArxivUserMenu/>}>
            <Toolbar sx={{display: 'flex', alignItems: 'center', width: '100%', mx: 0, minHeight: '32px !important',}}>
                {
                    isVerySmall ? null : (<>
                        <img src={"arxiv-logo.png"} alt="Arxiv Logo" style={{height: '14px', marginRight: '0px'}}/>
                            <Tooltip title={"Wombat"}>
                                <img src={"wombat-keyboard.png"} alt="Wombat" style={{height: '48px', marginRight: '2px'}}/>
                            </Tooltip>
                        </>
                    )
                }
                <ArxivNavMenu/>

                <Box sx={{flexGrow: 1}}/>
                <Tooltip title={(
                    <Typography variant="body1">
                        <p>Name search: Last name</p>
                        <p>Name search: "First name" "Last name"</p>
                        <p>Email search: foo@mit.edu</p>
                        <p>Username search: foo@</p>
                    </Typography>)}>
                    <TextField
                        variant="outlined"
                        size="small"
                        placeholder="Search user..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        onKeyDown={handleUserSearch}
                        helperText={null}
                        sx={{
                            minWidth: "8rem",
                            maxWidth: "25%",
                            mr: 1,
                            backgroundColor: theme.palette.background.default,
                            color: theme.palette.text.primary,
                            '& .MuiInputBase-input': {
                                color: theme.palette.text.primary
                            }
                        }}
                    />
                </Tooltip>

                <Tooltip title={(
                    <Typography variant="body1">
                        <p>Submission: nnnnnn</p>
                        <p>Submission: s/nnnnnn</p>
                        <p>Submission Title: {"s/<title>"}</p>
                        <p>Document: yymm.nnnnn</p>
                        <p>Document: category/nnnnnnn</p>
                        <p>Document: d/nnnnnn</p>
                        <p>Document Title: {"d/<title>"}</p>
                    </Typography>)}>
                    <TextField
                        size="small"
                        variant="outlined"
                        placeholder="Search subs/docs..."
                        value={docSearch}
                        onChange={(e) => setDocSearch(e.target.value)}
                        helperText={null}
                        onKeyDown={handleDocSearch}
                        sx={{
                            minWidth: "8rem",
                            maxWidth: "25%",
                            backgroundColor: theme.palette.background.default,
                            color: theme.palette.text.primary,
                            '& .MuiInputBase-input': {
                                color: theme.palette.text.primary
                            }
                        }}
                    />
                </Tooltip>

            </Toolbar>
            <PanelToggleButton/>
        </RaAppBar>
    );
};