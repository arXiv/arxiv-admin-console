import React, { useState } from 'react';

export interface CommentedConfirmProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (comment: string) => void,
    title: string;
    message: string;
    commentLabel: string;
}

import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField
} from '@mui/material';

const ConfirmWithComment: React.FC<CommentedConfirmProps> = (
    {open,
                                onClose,
                                onConfirm,
                                title = "Confirm Action",
                                message = "Are you sure?",
                                commentLabel = "Comment (optional)"
                            }) => {
    const [comment, setComment] = useState('');

    const handleConfirm = () => {
        onConfirm(comment);
        setComment('');
    };

    const handleClose = () => {
        onClose();
        setComment('');
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
                <p>{message}</p>
                <TextField
                    autoFocus
                    margin="dense"
                    label={commentLabel}
                    fullWidth
                    variant="outlined"
                    multiline
                    rows={3}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                />
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose}>Cancel</Button>
                <Button onClick={handleConfirm} variant="contained">
                    Confirm
                </Button>
            </DialogActions>
        </Dialog>
    );
};