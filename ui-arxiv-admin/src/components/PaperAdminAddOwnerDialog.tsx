import React, {useState} from "react";

import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
// import Checkbox from '@mui/material/Checkbox';

import {paths as adminApi} from '../types/admin-api';
import {Identifier, RecordContextProvider, useDataProvider, useNotify, useRefresh} from "react-admin";
// import MuiTextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";
import UserChooser from "./UserChooser";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import SingleUserInputField, { UserSelectDialog } from "./SingleUserInputField";
import Typography from "@mui/material/Typography";
import UserNameField from "../bits/UserNameField";
import UserStatusField from "../bits/UserStatusField";

type UpdatePaperOwnersRequestT = adminApi['/v1/paper_owners/authorship/{action}']['put']['requestBody']['content']['application/json'];
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
    const refresh = useRefresh();
    const [paperOwners, setPaperOwners] = useState<UserT[]>([]);
    const [isOwner, setIsOwner] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isUserSelectOpen, setIsUserSelectOpen] = useState(true);

    const handleSave = async (event: React.MouseEvent<HTMLButtonElement>) => {
        event.preventDefault();

        // Set saving state to disable the button
        setIsSaving(true);

        const ids = paperOwners.map((user) => `user_${user.id}-doc_${documentId}`);

        let data: UpdatePaperOwnersRequestT =
            {
                authored: isOwner ? ids : [],
                not_authored: isOwner ? [] : ids,
                auto: false
            };

        try {
            // Use update method for upsert operation
            await dataProvider.update('paper_owners/authorship', {
                id: 'upsert',
                data: data,
                previousData: {}
            });
            notify('Paper owners updated successfully', { type: 'success' });
            handleClose();
            refresh();
        } catch (error: any) {
            console.error("Error during save operations:", error);
            notify('Failed to update paper owners. ' + error?.detail, { type: 'error' });
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

    const onUsersSelected = (user: UserT) => {
        setPaperOwners([user]);
    }

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
            <UserSelectDialog
                open={isUserSelectOpen}
                onUserSelect={onUsersSelected}
                onClose={() => setIsUserSelectOpen(false)}
            />

            <DialogTitle>Add Paper Owner</DialogTitle>
            <DialogContent>
                <Box sx={{display: 'flex', flexDirection: 'column'}}>
                    <Box display="flex" flexDirection="row" sx={{gap: 1, flexWrap: 'wrap'}}>
                        <Button variant={"outlined"}  onClick={() => setIsUserSelectOpen(true)} disabled={isSaving} >User...</Button>

                    {
                        paperOwners.map((user) => {
                            return (
                                <RecordContextProvider value={user}>
                                    <UserNameField withEmail withUsername/>
                                    <UserStatusField source={"id"} />
                                </RecordContextProvider>
                            )
                        })
                    }
                    </Box>


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
