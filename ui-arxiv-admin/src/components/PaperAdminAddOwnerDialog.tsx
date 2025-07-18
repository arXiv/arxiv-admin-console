import React, {useState} from "react";

import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
// import Checkbox from '@mui/material/Checkbox';

import {paths as adminApi} from '../types/admin-api';
import {Identifier, useDataProvider, useNotify} from "react-admin";
// import MuiTextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";
import UserChooser from "./UserChooser";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";

type UpdatePaperOwnersRequestT = adminApi['/v1/paper_owners/update-paper-owners']['post']['requestBody']['content']['application/json'];
type UsersT = adminApi['/v1/users/']['get']['responses']['200']['content']['application/json'];
type UserT = UsersT[0];

const PaperAdminAddUserDialog: React.FC<
    {
        documentId?: Identifier;
        open: boolean;
        setOpen: (open: boolean) => void;
    }
> = ({documentId, open, setOpen }) => {
    if (!documentId) return null;

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const [paperOwners, setPaperOwners] = useState<string[]>([]);
    const [isOwner, setIsOwner] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async (event: React.MouseEvent<HTMLButtonElement>) => {
        event.preventDefault();

        // Set saving state to disable the button
        setIsSaving(true);

        const ids = paperOwners.map((user_id) => `user_${user_id}-doc_${documentId}`);

        let data: UpdatePaperOwnersRequestT =
            {
                document_id: documentId.toString(),
                owners: isOwner ? ids : [],
                nonowners: isOwner ? [] : ids,
                auto: false
            };

        try {
            await dataProvider.create('paper_owners/update-paper-owners', {data});
            notify('Paper owners updated successfully', { type: 'success' });
            handleClose();
        } catch (error) {
            console.error("Error during save operations:", error);
            notify('Failed to update paper owners', { type: 'error' });
        } finally {
            setIsSaving(false);
        }
    };

    const handleClose = () => {
        // Only allow closing if not in the middle of saving
        if (!isSaving) {
            setOpen(false);
        }
    };

    const onUsersSelected = (selectedUsers: UsersT) => {
        // @ts-ignore
        const owners = selectedUsers.filter((user: UserT) => user.id).map((user: UserT) => user.id.toString());
        console.log("Selected users:", JSON.stringify(selectedUsers));
        setPaperOwners(owners);
    }

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="md">
            <DialogTitle>Add Paper Owner</DialogTitle>
            <DialogContent>
                <Box sx={{display: 'flex', flexDirection: 'column'}}>
                    <UserChooser onUsersSelected={onUsersSelected}/>
                    <FormGroup>
                        <FormControlLabel
                            control={<Switch value={"isOwner"} checked={isOwner} onChange={() => setIsOwner(!isOwner)} />}
                            label="Owner" />
                    </FormGroup>
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={isSaving} >Cancel</Button>
                <Box sx={{flexGrow: 1}} />
                {(isSaving) ? <CircularProgress color="secondary"/> : null}
                <Button
                    onClick={handleSave}
                    variant="contained"
                    disabled={isSaving}
                >
                    {isSaving ? "Adding..." : "Add"}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default PaperAdminAddUserDialog;
