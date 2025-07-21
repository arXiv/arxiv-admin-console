import React from 'react';
import { Confirm } from 'react-admin';

const RenewPaperPasswordDialog: React.FC<{open: boolean, setOpen: (open: boolean) => void, renew: () => Promise<void>}> = ({open, setOpen, renew}) => {
    const handleConfirm = (): void => {
        // Do your action here
        console.log('User confirmed');
        setOpen(false);
        Promise.all([renew()]);
    };

    const handleCancel = (): void => {
        console.log('User cancelled');
        setOpen(false);
    };

    return (
            <Confirm
                isOpen={open}
                title="Renew Paper Password"
                content="Are you sure you want to renew the paper password?"
                onConfirm={handleConfirm}
                onClose={handleCancel}
            />
    );
};

export default RenewPaperPasswordDialog;