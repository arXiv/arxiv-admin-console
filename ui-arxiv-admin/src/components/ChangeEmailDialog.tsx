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
import {Identifier, useDataProvider, useNotify, useRecordContext} from "react-admin";
import { useContext } from "react";
import { RuntimeContext } from "../RuntimeContext";

interface ChangeEmailDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    onEmailChanged?: (newEmail: string) => void;
}

const ChangeEmailDialog: React.FC<ChangeEmailDialogProps> = (
    {
        open,
        setOpen,
        onEmailChanged
    }) => {
    const [newEmail, setNewEmail] = useState<string>("");
    const [confirmEmail, setConfirmEmail] = useState<string>("");
    const [reason, setReason] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const record = useRecordContext();

    const runtimeProps = useContext(RuntimeContext);

    // Reset form when dialog opens
    React.useEffect(() => {
        if (open) {
            setNewEmail("");
            setConfirmEmail("");
            setReason("");
            setError(null);
        }
    }, [open]);

    if (!record) return null;
    const userId = record.id as Identifier;
    const currentEmail = record.email;

    const handleClose = () => {
        if (!isLoading) {
            setOpen(false);
        }
    };

    const validateEmails = () => {
        if (!newEmail || !confirmEmail) {
            setError("Both email fields are required");
            return false;
        }

        if (newEmail !== confirmEmail) {
            setError("Emails do not match");
            return false;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(newEmail)) {
            setError("Please enter a valid email address");
            return false;
        }

        if (!reason.trim()) {
            setError("Please provide a reason for changing the email");
            return false;
        }

        return true;
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!validateEmails()) {
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            // Call the API to change the email
            await dataProvider.update('aaa_user_email', {
                id: userId,
                data: {
                    email: currentEmail,
                    new_email: newEmail,
                    comment: reason
                },
                previousData: {
                    email: currentEmail
                }
            });

            notify('Email successfully changed', { type: 'success' });

            // Call callback if provided
            if (onEmailChanged) {
                onEmailChanged(newEmail);
            }

            setOpen(false);
        } catch (error: any) {
            let message = error.message || "An error occurred while changing the email";
            if (error?.body?.detail) {
                message = message + ": " + error.body.detail;
            }
            console.error("Error changing email:", JSON.stringify(error));
            setError(message || "An error occurred while changing the email");
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
            aria-labelledby="change-email-dialog-title"
        >
            <form onSubmit={handleSubmit}>
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
                            value={newEmail}
                            onChange={(e) => setNewEmail(e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            autoFocus
                        />

                        <TextField
                            label="Confirm New Email Address"
                            type="email"
                            fullWidth
                            value={confirmEmail}
                            onChange={(e) => setConfirmEmail(e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            error={confirmEmail !== "" && newEmail !== confirmEmail}
                            helperText={confirmEmail !== "" && newEmail !== confirmEmail ? "Emails don't match" : ""}
                        />

                        <TextField
                            label="Reason for Change"
                            multiline
                            rows={3}
                            fullWidth
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
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
                        disabled={isLoading || !newEmail || !confirmEmail || newEmail !== confirmEmail || !reason.trim()}
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
