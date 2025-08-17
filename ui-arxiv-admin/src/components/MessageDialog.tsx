import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import {
    Dialog,
    DialogContent,
    DialogActions,
    DialogContentText,
    DialogTitle,
    Button,
} from "@mui/material";

interface MessageDialogState {
    open: boolean;
    title: string;
    message: string;
    onClose?: () => void;
}

interface MessageDialogContextType {
    showMessage: (title: string, message: string, onClose?: () => void) => void;
}

const MessageDialogContext = createContext<MessageDialogContextType | undefined>(undefined);

interface MessageDialogProviderProps {
    children: ReactNode;
}

const MessageDialogComponent: React.FC<{
    isOpen: boolean;
    title: string;
    content: string;
    onClose: () => void;
}> = ({ isOpen, title, content, onClose }) => {
    const handleClick = useCallback((e: React.MouseEvent) => {
        e.stopPropagation();
    }, []);

    return (
        <Dialog
            open={isOpen}
            onClose={onClose}
            onClick={handleClick}
            aria-labelledby="alert-dialog-title"
        >
            <DialogTitle id="alert-dialog-title">
                {title}
            </DialogTitle>
            <DialogContent>
                <DialogContentText >
                    {content}
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button
                    onClick={onClose} 
                    color="primary"
                    variant="contained"
                    autoFocus
                >
                    {'Close'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export const MessageDialogProvider: React.FC<MessageDialogProviderProps> = ({ children }) => {
    const [dialogState, setDialogState] = useState<MessageDialogState>({
        open: false,
        title: '',
        message: '',
        onClose: undefined
    });

    const showMessage = (title: string, message: string, onClose?: () => void) => {
        setDialogState({
            open: true,
            title,
            message,
            onClose
        });
    };

    const handleClose = () => {
        const { onClose } = dialogState;
        setDialogState(prev => ({ ...prev, open: false }));
        if (onClose) {
            onClose();
        }
    };

    return (
        <MessageDialogContext.Provider value={{ showMessage }}>
            {children}
            <MessageDialogComponent
                isOpen={dialogState.open}
                title={dialogState.title}
                content={dialogState.message}
                onClose={handleClose}
            />
        </MessageDialogContext.Provider>
    );
};

export const useMessageDialog = (): MessageDialogContextType => {
    const context = useContext(MessageDialogContext);
    if (!context) {
        throw new Error('useMessageDialog must be used within a MessageDialogProvider');
    }
    return context;
};