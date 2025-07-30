import React, { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogActions,
    DialogTitle,
    Button,
    TextField,
    Autocomplete,
    Box,
    Typography,
    CircularProgress,
    Chip
} from "@mui/material";
import {
    useDataProvider,
    useInput,
    InputProps,
    RaRecord
} from "react-admin";
import { paths as adminApi } from '../types/admin-api';

type UserType = adminApi['/v1/users/{user_id}']['get']['responses']['200']['content']['application/json'];

interface SingleUserInputFieldProps extends Omit<InputProps, 'source'> {
    source: string;
    label?: string;
    variant?: 'autocomplete' | 'dialog';
    placeholder?: string;
    required?: boolean;
}

interface UserSelectDialogProps {
    open: boolean;
    onClose: () => void;
    onUserSelect: (user: UserType) => void;
    selectedUserId?: number;
}

const UserSelectDialog: React.FC<UserSelectDialogProps> = ({
    open,
    onClose,
    onUserSelect,
    selectedUserId
}) => {
    const [nameQuery, setNameQuery] = useState("");
    const [emailQuery, setEmailQuery] = useState("");
    const [usernameQuery, setUsernameQuery] = useState("");
    const [users, setUsers] = useState<UserType[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedUser, setSelectedUser] = useState<UserType | null>(null);
    
    const dataProvider = useDataProvider();

    const searchUsers = async (name: string, email: string, username: string) => {
        const hasSearchTerms = name.trim() || email.trim() || username.trim();
        
        if (!hasSearchTerms) {
            setUsers([]);
            return;
        }

        setLoading(true);
        try {
            const filter: any = {};
            if (name.trim()) filter.name = name.trim();
            if (email.trim()) filter.email = email.trim();
            if (username.trim()) filter.username = username.trim();

            const result = await dataProvider.getList('users', {
                pagination: { page: 1, perPage: 50 },
                filter
            });
            setUsers(result.data);
        } catch (error) {
            console.error('Error searching users:', error);
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            searchUsers(nameQuery, emailQuery, usernameQuery);
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [nameQuery, emailQuery, usernameQuery]);

    const handleUserSelect = (user: UserType) => {
        setSelectedUser(user);
    };

    const handleConfirm = () => {
        if (selectedUser) {
            onUserSelect(selectedUser);
        }
        onClose();
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Select User</DialogTitle>
            <DialogContent>
                <Box sx={{ mb: 2, display: 'flex', gap: 2, flexDirection: 'row' }}>
                    <TextField
                        fullWidth
                        label="Name (First or Last)"
                        value={nameQuery}
                        onChange={(e) => setNameQuery(e.target.value)}
                        placeholder="Search by first or last name..."
                        variant="outlined"
                    />
                    <TextField
                        fullWidth
                        label="Email"
                        value={emailQuery}
                        onChange={(e) => setEmailQuery(e.target.value)}
                        placeholder="Search by email..."
                        variant="outlined"
                    />
                    <TextField
                        fullWidth
                        label="Username"
                        value={usernameQuery}
                        onChange={(e) => setUsernameQuery(e.target.value)}
                        placeholder="Search by username..."
                        variant="outlined"
                    />
                </Box>
                
                {loading && (
                    <Box display="flex" justifyContent="center" p={2}>
                        <CircularProgress />
                    </Box>
                )}

                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
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

                {(nameQuery || emailQuery || usernameQuery) && !loading && users.length === 0 && (
                    <Typography color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                        No users found matching your search criteria
                    </Typography>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                <Button 
                    onClick={handleConfirm} 
                    variant="contained"
                    disabled={!selectedUser}
                >
                    Select User
                </Button>
            </DialogActions>
        </Dialog>
    );
};

const SingleUserInputField: React.FC<SingleUserInputFieldProps> = ({
    source,
    label = "User",
    variant = 'autocomplete',
    placeholder,
    required = false,
    ...props
}) => {
    const { field } = useInput({ source, ...props });
    const [selectedUser, setSelectedUser] = useState<UserType | null>(null);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [autocompleteOptions, setAutocompleteOptions] = useState<UserType[]>([]);
    const [autocompleteLoading, setAutocompleteLoading] = useState(false);
    
    const dataProvider = useDataProvider();

    // Load selected user data when field value changes
    useEffect(() => {
        const loadSelectedUser = async () => {
            if (field.value) {
                try {
                    const result = await dataProvider.getOne('users', { id: field.value });
                    setSelectedUser(result.data);
                } catch (error) {
                    console.error('Error loading selected user:', error);
                    setSelectedUser(null);
                }
            } else {
                setSelectedUser(null);
            }
        };

        loadSelectedUser();
    }, [field.value, dataProvider]);

    const searchUsers = async (query: string) => {
        if (!query.trim()) {
            setAutocompleteOptions([]);
            return;
        }

        setAutocompleteLoading(true);
        try {
            const result = await dataProvider.getList('users', {
                pagination: { page: 1, perPage: 20 },
                filter: {
                    q: query
                }
            });
            setAutocompleteOptions(result.data);
        } catch (error) {
            console.error('Error searching users:', error);
            setAutocompleteOptions([]);
        } finally {
            setAutocompleteLoading(false);
        }
    };

    const handleUserSelect = (user: UserType) => {
        setSelectedUser(user);
        field.onChange(user.id);
    };

    const handleClear = () => {
        setSelectedUser(null);
        field.onChange(null);
    };

    if (variant === 'dialog') {
        return (
            <Box>
                <TextField
                    label={label}
                    value={selectedUser ? `${selectedUser.last_name}, ${selectedUser.first_name} (${selectedUser.username})` : ''}
                    placeholder={placeholder || "Click to select user"}
                    required={required}
                    onClick={() => setDialogOpen(true)}
                    InputProps={{
                        readOnly: true,
                        endAdornment: selectedUser && (
                            <Chip
                                size="small"
                                label="Clear"
                                onDelete={handleClear}
                                deleteIcon={<span>�</span>}
                            />
                        )
                    }}
                    fullWidth
                />
                <UserSelectDialog
                    open={dialogOpen}
                    onClose={() => setDialogOpen(false)}
                    onUserSelect={handleUserSelect}
                    selectedUserId={field.value}
                />
            </Box>
        );
    }

    // Autocomplete variant
    return (
        <Autocomplete
            value={selectedUser}
            onChange={(_, newValue) => {
                if (newValue) {
                    handleUserSelect(newValue);
                } else {
                    handleClear();
                }
            }}
            options={autocompleteOptions}
            getOptionLabel={(option) => `${option.last_name}, ${option.first_name} (${option.username})`}
            renderOption={(props, option) => (
                <Box component="li" {...props}>
                    <Box>
                        <Typography variant="body2">
                            {option.last_name}, {option.first_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            {option.username} " {option.email}
                        </Typography>
                    </Box>
                </Box>
            )}
            onInputChange={(_, newInputValue) => {
                searchUsers(newInputValue);
            }}
            loading={autocompleteLoading}
            renderInput={(params) => (
                <TextField
                    {...params}
                    label={label}
                    placeholder={placeholder || "Type to search users..."}
                    required={required}
                    InputProps={{
                        ...params.InputProps,
                        endAdornment: (
                            <>
                                {autocompleteLoading && <CircularProgress size={20} />}
                                {params.InputProps.endAdornment}
                            </>
                        ),
                    }}
                />
            )}
            fullWidth
        />
    );
};

export default SingleUserInputField;