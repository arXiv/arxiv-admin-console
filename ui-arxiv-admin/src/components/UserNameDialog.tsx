import React, { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogActions,
    DialogTitle,
    Button,
    Box,
    TextField,
    Typography,
    CircularProgress,
    Alert
} from "@mui/material";
import { Identifier, useDataProvider, useNotify, useRecordContext } from "react-admin";

interface UserNameDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    onUpdated?: () => void;
    title?: string;
    withUsername?: boolean;
}

const UserNameDialog: React.FC<UserNameDialogProps> = (
    {
        open,
        setOpen,
        onUpdated,
        title = "Update User Name",
        withUsername = false,
}) => {
    const [firstName, setFirstName] = useState<string>("");
    const [lastName, setLastName] = useState<string>("");
    const [suffixName, setSuffixName] = useState<string>("");
    const [username, setUsername] = useState<string>("");
    const [comment, setComment] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const record = useRecordContext();

    React.useEffect(() => {
        if (open && record) {
            setFirstName(record.first_name || "");
            setLastName(record.last_name || "");
            setSuffixName(record.suffix_name || "");
            setUsername(record.username || "");
            setComment("");
            setError(null);
        }
    }, [open, record]);

    if (!record) return null;
    const userId = record.id as Identifier;
    const currentName = `${record.first_name || ''} ${record.last_name || ''}`.trim() || record.username || `User ${userId}`;

    const handleClose = () => {
        if (!isLoading) {
            setOpen(false);
        }
    };

    const validateForm = () => {
        if (!firstName.trim() && !lastName.trim() && !username.trim()) {
            setError("Please provide at least a first name, last name, or username");
            return false;
        }
        if (!comment.trim()) {
            setError("Please provide a comment explaining this action");
            return false;
        }
        return true;
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!validateForm()) {
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const payload = {
                first_name: firstName.trim(),
                last_name: lastName.trim(),
                suffix_name: suffixName.trim(),
                username: username.trim(),
                comment: comment.trim()
            };

            await dataProvider.update('aaa_user_name', {
                id: userId,
                data: payload,
                previousData: record
            });

            const newName = `${firstName.trim()} ${lastName.trim()}`.trim();
            const message = `User name changed from '${currentName}' to '${newName}'`;
            notify(message, { type: 'success' });

            if (onUpdated) {
                onUpdated();
            }

            setOpen(false);
        } catch (error: any) {
            console.error("Error updating user name:", error);
            setError(error.message || "An error occurred while updating the user name");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            fullWidth
            maxWidth="sm"
            aria-labelledby="user-name-dialog-title"
        >
            <form onSubmit={handleSubmit}>
                <DialogTitle id="user-name-dialog-title">
                    {title}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body1" gutterBottom>
                            User: <strong>{currentName}</strong> (ID: {userId})
                        </Typography>

                        {error && (
                            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
                                {error}
                            </Alert>
                        )}

                        <TextField
                            label="First Name"
                            fullWidth
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            margin="normal"
                            disabled={isLoading}
                            placeholder="Enter first name"
                        />

                        <TextField
                            label="Last Name"
                            fullWidth
                            value={lastName}
                            onChange={(e) => setLastName(e.target.value)}
                            margin="normal"
                            disabled={isLoading}
                            placeholder="Enter last name"
                        />

                        <TextField
                            label="Suffix Name"
                            fullWidth
                            value={suffixName}
                            onChange={(e) => setSuffixName(e.target.value)}
                            margin="normal"
                            disabled={isLoading}
                            placeholder="Enter suffix (Jr., Sr., III, etc.)"
                        />

                        {
                            withUsername ? (
                                <TextField
                                    label="Username (Login Name)"
                                    fullWidth
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    margin="normal"
                                    disabled={isLoading}
                                    placeholder="Enter username"
                                />
                            ) : null
                        }

                        <TextField
                            label="Comment"
                            multiline
                            rows={4}
                            fullWidth
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            placeholder="Please provide a detailed explanation for this name change"
                            autoFocus
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button
                        onClick={handleClose}
                        disabled={isLoading}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        disabled={isLoading || !comment.trim() || (!firstName.trim() && !lastName.trim() && !username.trim())}
                        startIcon={isLoading ? <CircularProgress size={20} /> : null}
                    >
                        {isLoading ? "Updating..." : "Update Name"}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
};

export default UserNameDialog;