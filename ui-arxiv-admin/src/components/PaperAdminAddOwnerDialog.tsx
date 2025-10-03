import React, {useState, useEffect} from "react";

import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import TextField from '@mui/material/TextField';
import CircularProgress from "@mui/material/CircularProgress";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import Typography from "@mui/material/Typography";

import {paths as adminApi} from '../types/admin-api';
import {Identifier, RecordContextProvider, useDataProvider, useNotify, useRefresh} from "react-admin";
import UserNameField from "../bits/UserNameField";
import UserStatusField from "../bits/UserStatusField";

type UpdatePaperOwnersRequestT = adminApi['/v1/paper_owners/authorship/{action}']['put']['requestBody']['content']['application/json'];
type UsersT = adminApi['/v1/users/']['get']['responses']['200']['content']['application/json'];
type UserT = UsersT[0];

const PaperAdminAddUserDialog: React.FC<
    {
        documentId?: Identifier;
        open: boolean;
        setOpen: (open: boolean) => void;
    }
> = ({documentId, open, setOpen }) => {
    if (!documentId) return null;

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const refresh = useRefresh();
    const [paperOwners, setPaperOwners] = useState<UserT[]>([]);
    const [isOwner, setIsOwner] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [activeStep, setActiveStep] = useState(0);

    // User search state
    const [userIdQuery, setUserIdQuery] = useState("");
    const [nameQuery, setNameQuery] = useState("");
    const [emailQuery, setEmailQuery] = useState("");
    const [usernameQuery, setUsernameQuery] = useState("");
    const [users, setUsers] = useState<UserT[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedUser, setSelectedUser] = useState<UserT | null>(null);

    // Search users with debouncing
    useEffect(() => {
        const searchUsers = async (userId: string, name: string, email: string, username: string) => {
            const hasSearchTerms = userId.trim() || name.trim() || email.trim() || username.trim();

            if (!hasSearchTerms) {
                setUsers([]);
                return;
            }

            setLoading(true);
            try {
                const filter: any = {};
                if (userId.trim()) filter.id = userId.trim();
                if (name.trim()) filter.name = name.trim();
                if (email.trim()) filter.email = email.trim();
                if (username.trim()) filter.username = username.trim();

                const result = await dataProvider.getList('users', {
                    pagination: { page: 1, perPage: 50 },
                    filter
                });
                setUsers(result.data);

                // Auto-select if only one result
                if (result.data.length === 1) {
                    setSelectedUser(result.data[0]);
                    setPaperOwners([result.data[0]]);
                }
            } catch (error) {
                console.error('Error searching users:', error);
                setUsers([]);
            } finally {
                setLoading(false);
            }
        };

        const timeoutId = setTimeout(() => {
            searchUsers(userIdQuery, nameQuery, emailQuery, usernameQuery);
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [userIdQuery, nameQuery, emailQuery, usernameQuery, dataProvider]);

    const handleUserSelect = (user: UserT) => {
        setSelectedUser(user);
        setPaperOwners([user]);
    };

    const handleSave = async (event: React.MouseEvent<HTMLButtonElement>) => {
        event.preventDefault();

        // Set saving state to disable the button
        setIsSaving(true);

        const ids = paperOwners.map((user) => `user_${user.id}-doc_${documentId}`);

        let data: UpdatePaperOwnersRequestT =
            {
                authored: isOwner ? ids : [],
                not_authored: isOwner ? [] : ids,
                auto: false
            };

        try {
            // Use update method for upsert operation
            await dataProvider.update('paper_owners/authorship', {
                id: 'upsert',
                data: data,
                previousData: {}
            });
            notify('Paper owners updated successfully', { type: 'success' });
            handleClose();
            refresh();
        } catch (error: any) {
            console.error("Error during save operations:", error);
            notify('Failed to update paper owners. ' + error?.detail, { type: 'error' });
        } finally {
            setIsSaving(false);
        }
    };

    const handleClose = () => {
        // Only allow closing if not in the middle of saving
        if (!isSaving) {
            setOpen(false);
            setActiveStep(0);
            setPaperOwners([]);
            setIsOwner(true);
            setSelectedUser(null);
            setUserIdQuery("");
            setNameQuery("");
            setEmailQuery("");
            setUsernameQuery("");
            setUsers([]);
        }
    };

    const handleNext = () => {
        setActiveStep(1);
    };

    const handleBack = () => {
        setActiveStep(0);
    };

    const handleKeyDown = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && selectedUser && activeStep === 0) {
            event.preventDefault();
            handleNext();
        }
    };

    const steps = ['Select User', 'Set Ownership'];

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
            <DialogTitle>Add Paper Owner</DialogTitle>
            <DialogContent>
                <Stepper activeStep={activeStep} sx={{ pt: 2, pb: 3 }}>
                    {steps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                {activeStep === 0 && (
                    <Box sx={{display: 'flex', flexDirection: 'column', gap: 1, mt: 1}} onKeyDown={handleKeyDown}>
                        <Box sx={{ display: 'flex', gap: 1, flexDirection: 'column' }}>
                            <TextField
                                fullWidth
                                label="User ID"
                                value={userIdQuery}
                                onChange={(e) => setUserIdQuery(e.target.value)}
                                placeholder="Search by user ID..."
                                variant="outlined"
                                size="small"
                            />
                            <TextField
                                fullWidth
                                label="Name (First or Last)"
                                value={nameQuery}
                                onChange={(e) => setNameQuery(e.target.value)}
                                placeholder="Search by first or last name..."
                                variant="outlined"
                                size="small"
                            />
                            <TextField
                                fullWidth
                                label="Email"
                                value={emailQuery}
                                onChange={(e) => setEmailQuery(e.target.value)}
                                placeholder="Search by email..."
                                variant="outlined"
                                size="small"
                            />
                            <TextField
                                fullWidth
                                label="Username"
                                value={usernameQuery}
                                onChange={(e) => setUsernameQuery(e.target.value)}
                                placeholder="Search by username..."
                                variant="outlined"
                                size="small"
                            />
                        </Box>

                        {loading && (
                            <Box display="flex" justifyContent="center" p={2}>
                                <CircularProgress />
                            </Box>
                        )}

                        <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                            {users.map((user) => (
                                <Box
                                    key={user.id}
                                    sx={{
                                        p: 0.5,
                                        cursor: 'pointer',
                                        backgroundColor: selectedUser?.id === user.id ? 'action.selected' : 'transparent',
                                        '&:hover': {
                                            backgroundColor: 'action.hover'
                                        },
                                        borderRadius: 1,
                                        mb: 0.5,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 2
                                    }}
                                    onClick={() => handleUserSelect(user)}
                                >
                                    <Typography variant="body2" sx={{ minWidth: 80, fontWeight: 500 }}>
                                        ID: {user.id}
                                    </Typography>
                                    <Typography variant="body2" sx={{ minWidth: 150 }}>
                                        {user.last_name}, {user.first_name}
                                    </Typography>
                                    <Typography variant="body2" sx={{ minWidth: 120 }}>
                                        {user.username}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
                                        {user.email}
                                    </Typography>
                                </Box>
                            ))}
                        </Box>

                        {(userIdQuery || nameQuery || emailQuery || usernameQuery) && !loading && users.length === 0 && (
                            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                                No users found matching your search criteria
                            </Typography>
                        )}

                        {selectedUser && (
                            <Box display="flex" flexDirection="column" sx={{gap: 1, mt: 2}}>
                                <Typography variant="body2" color="text.secondary">Selected user:</Typography>
                                <RecordContextProvider value={selectedUser}>
                                    <Box>
                                        <UserNameField withEmail withUsername/>
                                        <UserStatusField source={"id"} />
                                    </Box>
                                </RecordContextProvider>
                            </Box>
                        )}
                    </Box>
                )}

                {activeStep === 1 && (
                    <Box sx={{display: 'flex', flexDirection: 'column', gap: 2, mt: 2}}>
                        <Box display="flex" flexDirection="column" sx={{gap: 1}}>
                            <Typography variant="body2" color="text.secondary">Selected user:</Typography>
                            {paperOwners.map((user) => (
                                <RecordContextProvider key={user.id} value={user}>
                                    <Box>
                                        <UserNameField withEmail withUsername/>
                                        <UserStatusField source={"id"} />
                                    </Box>
                                </RecordContextProvider>
                            ))}
                        </Box>
                        <FormGroup>
                            <FormControlLabel
                                control={<Switch value={"isOwner"} checked={isOwner} onChange={() => setIsOwner(!isOwner)} />}
                                label="Owner"
                            />
                        </FormGroup>
                    </Box>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={isSaving}>Cancel</Button>
                <Box sx={{flexGrow: 1}} />
                {isSaving && <CircularProgress color="secondary" size={24} />}
                {activeStep === 0 && (
                    <Button
                        onClick={handleNext}
                        variant="contained"
                        disabled={paperOwners.length === 0}
                    >
                        Next
                    </Button>
                )}
                {activeStep === 1 && (
                    <>
                        <Button onClick={handleBack} disabled={isSaving}>
                            Back
                        </Button>
                        <Button
                            onClick={handleSave}
                            variant="contained"
                            disabled={isSaving}
                        >
                            {isSaving ? "Adding..." : "Add"}
                        </Button>
                    </>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default PaperAdminAddUserDialog;
