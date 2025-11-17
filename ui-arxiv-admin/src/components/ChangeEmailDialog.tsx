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

interface ChangeEmailDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    onEmailChanged?: (newEmail: string) => void;
}

interface EmailFormValues {
    newEmail: string;
    confirmEmail: string;
    reason: string;
}

const ChangeEmailDialog: React.FC<ChangeEmailDialogProps> = ({
    open,
    setOpen,
    onEmailChanged
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
    } = useChangeDialog<EmailFormValues>({
        open,
        getInitialValues: () => ({
            newEmail: "",
            confirmEmail: "",
            reason: "",
        }),
        validate: (values) => {
            if (!values.newEmail || !values.confirmEmail) {
                return "Both email fields are required";
            }
            if (values.newEmail !== values.confirmEmail) {
                return "Emails do not match";
            }
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(values.newEmail)) {
                return "Please enter a valid email address";
            }
            if (!values.reason.trim()) {
                return "Please provide a reason for changing the email";
            }
            return null;
        },
        resource: 'aaa_user_email',
        transformPayload: (values, record) => ({
            email: record.email,
            new_email: values.newEmail,
            comment: values.reason,
        }),
        successMessage: 'Email successfully changed',
        onSuccess: (values) => {
            if (onEmailChanged) {
                onEmailChanged(values.newEmail);
            }
            setOpen(false);
        },
    });

    if (!record) return null;

    const currentEmail = record.email;

    const handleClose = () => {
        if (!isLoading) {
            setOpen(false);
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
            aria-labelledby="change-email-dialog-title"
        >
            <form onSubmit={onSubmit}>
                <DialogTitle id="change-email-dialog-title">
                    Change User Email Address
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Current Email: <strong>{currentEmail}</strong>
                        </Typography>

                        {error && (
                            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
                                {error}
                            </Alert>
                        )}

                        <TextField
                            label="New Email Address"
                            type="email"
                            fullWidth
                            value={values.newEmail || ''}
                            onChange={(e) => setValue('newEmail', e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            autoFocus
                        />

                        <TextField
                            label="Confirm New Email Address"
                            type="email"
                            fullWidth
                            value={values.confirmEmail || ''}
                            onChange={(e) => setValue('confirmEmail', e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            error={values.confirmEmail !== "" && values.newEmail !== values.confirmEmail}
                            helperText={values.confirmEmail !== "" && values.newEmail !== values.confirmEmail ? "Emails don't match" : ""}
                        />

                        <TextField
                            label="Reason for Change"
                            multiline
                            rows={3}
                            fullWidth
                            value={values.reason || ''}
                            onChange={(e) => setValue('reason', e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            placeholder="Please provide a detailed reason for this email change"
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
                        disabled={isLoading || !values.newEmail || !values.confirmEmail || values.newEmail !== values.confirmEmail || !values.reason?.trim()}
                        startIcon={isLoading ? <CircularProgress size={20} /> : null}
                    >
                        {isLoading ? "Changing..." : "Change Email"}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
};

export default ChangeEmailDialog;
