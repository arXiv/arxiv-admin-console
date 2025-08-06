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

export interface UserFlagOption {
    key: string;
    label: string;
    description?: string;
}

interface UserFlagDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    onUpdated?: () => void;
    title?: string;
    initialFlag?: string;
    flagOptions?: UserFlagOption[];
    pendingValue?: boolean | null;
}

const defaultFlagOptions: UserFlagOption[] = [
    { key: "flag_suspect", label: "Flagged/Suspect", description: "Mark user as suspect for review" },
    { key: "flag_banned", label: "Banned", description: "Ban user from the system" },
    { key: "flag_deleted", label: "Deleted", description: "Mark user as deleted" },
    { key: "flag_approved", label: "Approved", description: "Mark user as approved" },
    { key: "flag_veto_status", label: "Veto Status", description: "Set veto status" },
    { key: "flag_proxy", label: "Proxy", description: "Mark as proxy user" },
    { key: "flag_xml", label: "XML", description: "XML processing flag" },
    { key: "flag_allow_tex_produced", label: "Allow TeX", description: "Allow TeX produced submissions" },
    { key: "flag_edit_users", label: "Edit Users", description: "Can edit users (admin)" },
    { key: "flag_edit_system", label: "Edit System", description: "Can edit system (admin)" },
    { key: "flag_group_test", label: "Test", description: "Test group member" },
    { key: "flag_internal", label: "Internal", description: "Internal user" },
    { key: "flag_can_lock", label: "Can Lock", description: "Can lock submissions" },
    { key: "flag_email_verified", label: "Email Verified", description: "Email address verified" },
    { key: "email_bouncing", label: "Email Bouncing", description: "Email address is bouncing" },
    { key: "flag_is_mod", label: "Moderator", description: "User is a moderator" }
];

const UserFlagDialog: React.FC<UserFlagDialogProps> = ({
    open,
    setOpen,
    onUpdated,
    title = "Update User Flag",
    initialFlag = "",
    flagOptions = defaultFlagOptions,
    pendingValue = null
}) => {
    const [selectedFlag, setSelectedFlag] = useState<string>("");
    const [flagValue, setFlagValue] = useState<boolean>(true);
    const [comment, setComment] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const record = useRecordContext();

    // Reset form when dialog opens
    React.useEffect(() => {
        if (open) {
            setSelectedFlag(initialFlag);
            setFlagValue(pendingValue !== null ? pendingValue : true);
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

    const handleFlagChange = (event: SelectChangeEvent) => {
        setSelectedFlag(event.target.value);
    };

    const validateForm = () => {
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
            if (flagOptions.length > 0) {
                // Prepare payload for custom endpoint
                const payload =
                    {
                        property_name: selectedFlag || null,
                        property_value: selectedFlag ? flagValue : null,
                        comment: comment.trim()
                    };

                // Use dataProvider's custom method to call: PUT /users/{id}/demographic
                await dataProvider.update('users', {
                    id: `${userId}/demographic`,
                    data: payload,
                    previousData: record
                });

                const flagLabel = selectedFlag ? flagOptions.find(opt => opt.key === selectedFlag)?.label : null;
                const message = `User ${userName} flag '${flagLabel}' set to ${flagValue ? 'ON' : 'OFF'}`;
                notify(message, { type: 'success' });

                // Call callback if provided
                if (onUpdated) {
                    onUpdated();
                }
            }
            else {
                // Prepare payload for custom endpoint
                const payload = {comment: comment.trim()};

                // Use dataProvider's custom method to call: PUT /users/{id}/demographic
                await dataProvider.create('user-comment', {
                    data: payload,
                    meta: {userId: userId},
                });

                const message = `Comment added for user ${userName}`;

                notify(message, { type: 'info' });

                // Call callback if provided
                if (onUpdated) {
                    onUpdated();
                }
            }

            setOpen(false);
        } catch (error: any) {
            console.error("Error updating user flag:", error);
            setError(error.message || "An error occurred while updating the user");
        } finally {
            setIsLoading(false);
        }
    };

    const selectedFlagOption = flagOptions.find(opt => opt.key === selectedFlag);

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            fullWidth
            maxWidth="sm"
            aria-labelledby="user-flag-dialog-title"
        >
            <form onSubmit={handleSubmit}>
                <DialogTitle id="user-flag-dialog-title">
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

                        {flagOptions.length > 0 && (
                            <FormControl fullWidth margin="normal">
                                <InputLabel>Flag to Update</InputLabel>
                                <Select
                                    value={selectedFlag}
                                    onChange={handleFlagChange}
                                    label="Flag to Update (Optional)"
                                    disabled={isLoading}
                                >
                                    <MenuItem value="">
                                        <em>No flag change - comment only</em>
                                    </MenuItem>
                                    {flagOptions.map((option) => (
                                        <MenuItem key={option.key} value={option.key}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}

                        {selectedFlag && (
                            <FormControl fullWidth margin="normal">
                                <InputLabel>Flag Value</InputLabel>
                                <Select
                                    value={flagValue.toString()}
                                    onChange={(e) => setFlagValue(e.target.value === 'true')}
                                    label="Flag Value"
                                    disabled={isLoading}
                                >
                                    <MenuItem value="true">ON (True)</MenuItem>
                                    <MenuItem value="false">OFF (False)</MenuItem>
                                </Select>
                            </FormControl>
                        )}

                        {selectedFlagOption?.description && (
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
                                {selectedFlagOption.description}
                            </Typography>
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
                        {isLoading ? "Updating..." : selectedFlag ? "Update Flag" : "Add Comment"}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
};

export default UserFlagDialog;