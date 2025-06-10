import React from 'react';
import {
    AppBar as RaAppBar,
    TitlePortal,
} from 'react-admin';
import TextField from '@mui/material/TextField';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const AdminConsoleAppBar = () => {
    const [userSearch, setUserSearch] = useState('');
    const [docSearch, setDocSearch] = useState('');
    const navigate = useNavigate();

    const handleUserSearch = (e: React.KeyboardEvent) => {
        let criteria = {}
        const searchTerm = userSearch.trim();
        if (e.key === 'Enter' && searchTerm) {
            if (searchTerm.includes('@')) {
                criteria = {email: searchTerm}
            }
            else {
                const terms = userSearch.trim().split(" ");
                criteria = (terms.length > 1) ? {first_name: terms[0], last_name: terms[1]} : {first_name: terms[0], last_name: terms[1]}
            }
            const filter = encodeURIComponent(JSON.stringify(criteria));
            navigate(`/users?filter=${filter}`);
        }
    };

    const handleDocSearch = (e: React.KeyboardEvent) => {
        const searchTerm = docSearch.trim();
        if (e.key === 'Enter' && searchTerm) {
            if (searchTerm.includes('/') || searchTerm.includes('.')) {
                navigate(`/documents/${searchTerm}`);
            }
            else {
                const criteria = {id: searchTerm}
                const filter = encodeURIComponent(JSON.stringify(criteria));
                // navigate(`/submissions?filter=${filter}}`);
                navigate(`/submissions/${searchTerm}`);
            }
        }
    };

    return (
        <RaAppBar>
            <Toolbar sx={{ display: 'flex', alignItems: 'center', width: '100%', mx: 1 , minHeight: '48px !important',}}>
                <TitlePortal />
                    <Box sx={{flexGrow: 1 }} />
                    <TextField
                        variant="outlined"
                        size="small"
                        placeholder="Search user..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        onKeyDown={handleUserSearch}
                        helperText={null}
                        sx={{maxWidth: "300px", mr: 1}}
                    />

                    <TextField
                        size="small"
                        variant="outlined"
                        placeholder="Search subs/docs..."
                        value={docSearch}
                        onChange={(e) => setDocSearch(e.target.value)}
                        helperText={null}
                        onKeyDown={handleDocSearch}
                        sx={{maxWidth: "300px"}}
                    />
            </Toolbar>
        </RaAppBar>
    );
};
