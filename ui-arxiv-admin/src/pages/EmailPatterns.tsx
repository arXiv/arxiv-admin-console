import {
    List,
    Datagrid,
    TextField,
    EditButton,
    Edit,
    Create,
    SimpleForm,
    TextInput,
    useRecordContext,
    Filter,
    SelectInput,
    useListContext,
    Pagination,
    BulkDeleteButton,
    useDataProvider,
    useNotify,
    useUnselectAll,
    useRefresh,
    TopToolbar,
    CreateButton,
    ExportButton
} from 'react-admin';
import { Button, Box, Menu, MenuItem, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadIcon from '@mui/icons-material/Upload';
import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { useState, useContext } from 'react';
import { EmailPatternUploadDialog } from '../components/EmailPatternUploadDialog';
import { EmailPatternDownloadDialog } from '../components/EmailPatternDownloadDialog';
import { RuntimeContext } from '../RuntimeContext';
import {emailPatternPurposeOptions} from "../types/definitions";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";

const EmailPatternFilter = (props: any) => {
    return (
        <Filter {...props}>
            <SelectInput
                label="Purpose"
                source="purpose"
                choices={emailPatternPurposeOptions.slice(1)}
                alwaysOn
                emptyValue={emailPatternPurposeOptions[0].id}
                emptyText={emailPatternPurposeOptions[0].name}
                sx={{ minWidth: "8rem" }}
            />
            <TextInput label={"Pattern"} source={"pattern"} alwaysOn/>
        </Filter>
    );
};

// Custom bulk delete button that includes purpose in the path
const EmailPatternBulkDeleteButton = () => {
    const dataProvider = useDataProvider();
    const notify = useNotify();
    const refresh = useRefresh();
    const unselectAll = useUnselectAll('email_patterns');
    const { selectedIds, data } = useListContext();

    const handleClick = async () => {
        if (selectedIds.length > 0 && data) {
            try {
                const purpose = data[0].purpose;
                console.log(`Deleting ${selectedIds.length} email patterns for purpose ${purpose}`);
                // Delete records grouped by purpose
                await dataProvider.deleteMany('email_patterns', {
                    ids: selectedIds,
                    meta: {purpose}
                });
                notify(`${selectedIds.length} email patterns deleted`, {type: 'info'});
            } catch (error) {
                notify('Error deleting email patterns', {type: 'error'});
            }
            unselectAll();
            refresh();
        }
    };

    return (
        <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleClick}
            disabled={selectedIds.length === 0}
            size="small"
        >
            Delete ({selectedIds.length})
        </Button>
    );
};

// Custom pagination with rows per page selector
const EmailPatternPagination = () => <Pagination rowsPerPageOptions={[10, 25, 50, 100]} />;

// Custom list actions with create, export and hamburger menu
const EmailPatternListActions = () => {
    const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
    const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const menuOpen = Boolean(anchorEl);

    const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleUploadClick = () => {
        setUploadDialogOpen(true);
        handleMenuClose();
    };

    const handleDownloadClick = () => {
        setDownloadDialogOpen(true);
        handleMenuClose();
    };

    return (
        <TopToolbar>
            <CreateButton />
            <ExportButton />
            <IconButton
                onClick={handleMenuClick}
                sx={{ ml: 1 }}
                aria-label="more actions"
            >
                <MoreVertIcon />
            </IconButton>
            <Menu
                anchorEl={anchorEl}
                open={menuOpen}
                onClose={handleMenuClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
            >
                <MenuItem onClick={handleUploadClick}>
                    <UploadIcon sx={{ mr: 1 }} />
                    Bulk Upload
                </MenuItem>
                <MenuItem onClick={handleDownloadClick}>
                    <DownloadIcon sx={{ mr: 1 }} />
                    Bulk Download
                </MenuItem>
            </Menu>
            <EmailPatternUploadDialog
                open={uploadDialogOpen}
                onClose={() => setUploadDialogOpen(false)}
            />
            <EmailPatternDownloadDialog
                open={downloadDialogOpen}
                onClose={() => setDownloadDialogOpen(false)}
            />
        </TopToolbar>
    );
};

export const EmailPatternList = () => (
<>
    <ConsoleTitle>Email Patterns</ConsoleTitle>
    <List
        filters={<EmailPatternFilter/>} 
        filterDefaultValues={{purpose: 'black'}}
        actions={<EmailPatternListActions />}
    >
        <Datagrid rowClick={false} bulkActionButtons={<EmailPatternBulkDeleteButton />}>
            <TextField source="id" label="Pattern" />
        </Datagrid>
    </List>
</>
);

export const EmailPatternCreate = () => (
    <Create>
        <ConsoleTitle>Add Pattern</ConsoleTitle>
        <SimpleForm>
            <TextInput source="id" label="Pattern" />
            <SelectInput 
                source="purpose" 
                choices={emailPatternPurposeOptions}
                label="Purpose"
            />
        </SimpleForm>
    </Create>
);
