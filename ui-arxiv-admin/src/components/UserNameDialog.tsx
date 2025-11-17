import React from "react";
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
import { useChangeDialog } from "../hooks/useChangeDialog";

interface UserNameDialogProps {
    open: boolean;
    setOpen: (open : 'closed' | 'name' | 'username') => void;
    onUpdated?: () => void;
    title?: string;
    withUsername?: boolean;
}

interface UserNameFormValues {
    firstName?: string;
    lastName?: string;
    suffixName?: string;
    username?: string;
    comment: string;
}

const UserNameDialog: React.FC<UserNameDialogProps> = ({
    open,
    setOpen,
    onUpdated,
    title = "Update User",
    withUsername = false,
}) => {
    const {
        values,
        setValue,
        isLoading,
        error,
        setError,
        record,
        userId,
        handleSubmit,
    } = useChangeDialog<UserNameFormValues>({
        open,
        getInitialValues: (record) => ({
            firstName: record.first_name || "",
            lastName: record.last_name || "",
            suffixName: record.suffix_name || "",
            username: record.username || "",
            comment: "",
        }),
        validate: (values) => {
            if (!values.firstName?.trim() && !values.lastName?.trim() && !values.username?.trim()) {
                return "Please provide at least a first name, last name, or username";
            }
            if (!values.comment.trim()) {
                return "Please provide a comment explaining this action";
            }
            return null;
        },
        resource: 'aaa_user_name',
        transformPayload: (values) => ({
            first_name: !withUsername ? values.firstName?.trim() : undefined,
            last_name: !withUsername ? values.lastName?.trim() : undefined,
            suffix_name: !withUsername ? values.suffixName?.trim() : undefined,
            username: withUsername ? values.username?.trim() : undefined,
            comment: values.comment.trim(),
        }),
        successMessage: (values, record) => {
            const currentName = `${record.first_name || ''} ${record.last_name || ''}`.trim() || record.username || `User ${record.id}`;
            const newName = `${values.firstName?.trim()} ${values.lastName?.trim()}`.trim();
            return `User name changed from '${currentName}' to '${newName}'`;
        },
        onSuccess: () => {
            if (onUpdated) {
                onUpdated();
            }
            setOpen('closed');
        },
    });

    if (!record) return null;

    const currentName = `${record.first_name || ''} ${record.last_name || ''}`.trim() || record.username || `User ${userId}`;

    const handleClose = () => {
        if (!isLoading) {
            setOpen('closed');
        }
    };

    const onSubmit = async (event: React.FormEvent) => {
        await handleSubmit(event);
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            fullWidth
            maxWidth="sm"
            aria-labelledby="user-name-dialog-title"
        >
            <form onSubmit={onSubmit}>
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

                        {!withUsername && (
                            <TextField
                                label="First Name"
                                fullWidth
                                value={values.firstName || ''}
                                onChange={(e) => setValue('firstName', e.target.value)}
                                margin="normal"
                                disabled={isLoading}
                                placeholder="Enter first name"
                            />
                        )}

                        {!withUsername && (
                            <TextField
                                label="Last Name"
                                fullWidth
                                value={values.lastName || ''}
                                onChange={(e) => setValue('lastName', e.target.value)}
                                margin="normal"
                                disabled={isLoading}
                                placeholder="Enter last name"
                            />
                        )}

                        {!withUsername && (
                            <TextField
                                label="Suffix Name"
                                fullWidth
                                value={values.suffixName || ''}
                                onChange={(e) => setValue('suffixName', e.target.value)}
                                margin="normal"
                                disabled={isLoading}
                                placeholder="Enter suffix (Jr., Sr., III, etc.)"
                            />
                        )}

                        {withUsername && (
                            <TextField
                                label="Username (Login Name)"
                                fullWidth
                                value={values.username || ''}
                                onChange={(e) => setValue('username', e.target.value)}
                                margin="normal"
                                disabled={isLoading}
                                placeholder="Enter username"
                            />
                        )}

                        <TextField
                            label="Comment"
                            multiline
                            rows={4}
                            fullWidth
                            value={values.comment || ''}
                            onChange={(e) => setValue('comment', e.target.value)}
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
                        disabled={isLoading || !values.comment?.trim() || (!(values.firstName?.trim()) && !(values.lastName?.trim()) && !(values.username?.trim()))}
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
