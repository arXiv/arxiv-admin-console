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

interface ChangePasswordDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    onPasswordChanged?: () => void;
    requireConfirmation?: boolean;
}

const ChangePasswordDialog: React.FC<ChangePasswordDialogProps> = (
    {
        open,
        setOpen,
        onPasswordChanged,
        requireConfirmation = false
    }) => {
    const [newPassword, setNewPassword] = useState<string>("");
    const [confirmPassword, setConfirmPassword] = useState<string>("");
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
            setNewPassword("");
            setConfirmPassword("");
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

    const validatePasswords = () => {
        if (!newPassword) {
            setError("New password is required");
            return false;
        }

        if (requireConfirmation && !confirmPassword) {
            setError("Please confirm the password");
            return false;
        }

        if (requireConfirmation && newPassword !== confirmPassword) {
            setError("Passwords do not match");
            return false;
        }

        if (newPassword.length < 8) {
            setError("Password must be at least 8 characters long");
            return false;
        }

        if (!reason.trim()) {
            setError("Please provide a reason for changing the password");
            return false;
        }

        return true;
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!validatePasswords()) {
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            // Call the API to change the password
            await dataProvider.update('aaa_user_password', {
                id: userId,
                data: {
                    email: currentEmail,
                    new_password: newPassword,
                    comment: reason
                },
                previousData: {
                    email: currentEmail
                }
            });

            notify('Password successfully changed', { type: 'success' });

            // Call callback if provided
            if (onPasswordChanged) {
                onPasswordChanged();
            }

            setOpen(false);
        } catch (error: any) {
            let message = error.message || "An error occurred while changing the password";
            if (error?.body?.detail) {
                message = message + ": " + error.body.detail;
            }
            console.error("Error changing password:", JSON.stringify(error));
            setError(message || "An error occurred while changing the password");
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
            aria-labelledby="change-password-dialog-title"
        >
            <form onSubmit={handleSubmit}>
                <DialogTitle id="change-password-dialog-title">
                    Change User Password
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            User: <strong>{currentEmail}</strong>
                        </Typography>

                        {error && (
                            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
                                {error}
                            </Alert>
                        )}

                        <TextField
                            label="New Password"
                            type="password"
                            fullWidth
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            margin="normal"
                            required
                            disabled={isLoading}
                            autoFocus
                        />

                        {requireConfirmation && (
                            <TextField
                                label="Confirm New Password"
                                type="password"
                                fullWidth
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                margin="normal"
                                required
                                disabled={isLoading}
                                error={confirmPassword !== "" && newPassword !== confirmPassword}
                                helperText={confirmPassword !== "" && newPassword !== confirmPassword ? "Passwords don't match" : ""}
                            />
                        )}

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
                            placeholder="Please provide a detailed reason for this password change"
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
                        disabled={isLoading || !newPassword || (requireConfirmation && (!confirmPassword || newPassword !== confirmPassword)) || !reason.trim()}
                        startIcon={isLoading ? <CircularProgress size={20} /> : null}
                    >
                        {isLoading ? "Changing..." : "Change Password"}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
};

export default ChangePasswordDialog;