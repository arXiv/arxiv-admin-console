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
    Alert,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    SelectChangeEvent
} from "@mui/material";
import { Identifier, useDataProvider, useNotify, useRecordContext } from "react-admin";


interface UserAddCommentDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    onCommentAdded?: () => void;
    title?: string;
    initialFlag?: string;
    pendingValue?: boolean | null;
}


const UserAddCommentDialog: React.FC<UserAddCommentDialogProps> = (
    { open, setOpen, onCommentAdded,
        title = "Add Comment",
        initialFlag = "",
        pendingValue = null
    }) => {
    const [comment, setComment] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const record = useRecordContext();

    // Reset form when dialog opens
    React.useEffect(() => {
        if (open) {
            setComment("");
            setError(null);
        }
    }, [open, initialFlag, pendingValue]);

    if (!record) return null;
    const userId = record.id as Identifier;
    const userName = `${record.first_name || ''} ${record.last_name || ''}`.trim() || record.username || `User ${userId}`;

    const handleClose = () => {
        if (!isLoading) {
            setOpen(false);
        }
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        setIsLoading(true);
        setError(null);

        try {
            // Prepare payload for custom endpoint
            const payload = {
                comment: comment.trim()
            };

            // Use dataProvider's custom method to call: PUT /users/{id}/property
            await dataProvider.update('users', {
                id: `${userId}/comment`,
                data: payload,
                previousData: record
            });

            const message = "Comment added for user " + userName;
            notify(message, { type: 'success' });
            setOpen(false);
        } catch (error: any) {
            console.error("Error updating user flag:", error);
            setError(error.message || "An error occurred while updating the user");
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
            aria-labelledby="user-flag-dialog-title"
        >
            <form onSubmit={handleSubmit}>
                <DialogTitle id="user-add-comment-dialog-title">
                    {title}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body1" gutterBottom>
                            User: <strong>{userName}</strong> (ID: {userId})
                        </Typography>

                        {error && (
                            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
                                {error}
                            </Alert>
                        )}

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
                            placeholder="Please provide a detailed explanation for this action"
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
                        disabled={isLoading || !comment.trim()}
                        startIcon={isLoading ? <CircularProgress size={20} /> : null}
                    >
                        {"Add Comment"}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
};

export default UserAddCommentDialog;