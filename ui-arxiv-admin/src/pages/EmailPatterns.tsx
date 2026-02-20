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
import {Button, Box, Menu, MenuItem, IconButton} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadIcon from '@mui/icons-material/Upload';
import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import {useState, useContext} from 'react';
import {useSearchParams} from 'react-router-dom';
import {EmailPatternUploadDialog} from '../components/EmailPatternUploadDialog';
import {EmailPatternDownloadDialog} from '../components/EmailPatternDownloadDialog';
import {RuntimeContext} from '../RuntimeContext';
import {emailPatternPurposeOptions} from "../types/definitions";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AccordionDetails from "@mui/material/AccordionDetails";

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
                sx={{minWidth: "8rem"}}
            />
            <TextInput label={"Domains"} source={"domains"} alwaysOn/>
        </Filter>
    );
};

// Custom bulk delete button that includes purpose in the path
const EmailPatternBulkDeleteButton = () => {
    const dataProvider = useDataProvider();
    const notify = useNotify();
    const refresh = useRefresh();
    const unselectAll = useUnselectAll('email_patterns');
    const {selectedIds, data} = useListContext();

    const handleClick = async () => {
        if (selectedIds.length > 0 && data) {
            try {
                const purpose = data[0].purpose;
                console.log(`Deleting ${selectedIds.length} email domains for purpose ${purpose}`);
                // Delete records grouped by purpose
                await dataProvider.deleteMany('email_patterns', {
                    ids: selectedIds,
                    meta: {purpose}
                });
                notify(`${selectedIds.length} email domains deleted`, {type: 'info'});
            } catch (error) {
                notify('Error deleting email domains', {type: 'error'});
            }
            unselectAll();
            refresh();
        }
    };

    return (
        <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon/>}
            onClick={handleClick}
            disabled={selectedIds.length === 0}
            size="small"
        >
            Delete ({selectedIds.length})
        </Button>
    );
};

// Custom pagination with rows per page selector
const EmailPatternPagination = () => <Pagination rowsPerPageOptions={[10, 25, 50, 100]}/>;

// Custom list actions with create, export and hamburger menu
const EmailPatternListActions = () => {
    const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
    const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const menuOpen = Boolean(anchorEl);
    const { filterValues } = useListContext();
    const currentPurpose = filterValues?.purpose || 'black';

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
            <CreateButton to={`/email_patterns/create?purpose=${currentPurpose}`}/>
            <ExportButton/>
            <IconButton
                onClick={handleMenuClick}
                sx={{ml: 1}}
                aria-label="more actions"
            >
                <MoreVertIcon/>
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
                    <UploadIcon sx={{mr: 1}}/>
                    Bulk Upload
                </MenuItem>
                <MenuItem onClick={handleDownloadClick}>
                    <DownloadIcon sx={{mr: 1}}/>
                    Bulk Download
                </MenuItem>
            </Menu>
            <EmailPatternUploadDialog
                open={uploadDialogOpen}
                onClose={() => setUploadDialogOpen(false)}
                defaultPurpose={currentPurpose}
            />
            <EmailPatternDownloadDialog
                open={downloadDialogOpen}
                onClose={() => setDownloadDialogOpen(false)}
                defaultPurpose={currentPurpose}
            />
        </TopToolbar>
    );
};

export const EmailPatternList = () => (
    <Box maxWidth={"lg"} sx={{margin: '0 auto'}}>
        <ConsoleTitle>Email Domains</ConsoleTitle>
        <Accordion defaultExpanded sx={{mt: 0, pt: 0}}>
            <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="email-domain-description"
                id="email-domain-descriptionr"
                sx={{ minHeight: 0, '&.Mui-expanded': { minHeight: 0 }, '& .MuiAccordionSummary-content': { my: 0.5 }, '& .MuiAccordionSummary-content.Mui-expanded': { my: 0.5 } }}
            >
                <Typography component="span" fontSize={"1.2em"}>Email domain patterns used for configuring account and auto-endorsement.</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{p: '0'}}>
                <Typography component="div" fontSize={"1.1em"}>
                    <ul>
                        <li>Block list - email patterns that block account creation</li>
                        <li>White list - recognized research institutions domains or auto-endorsement</li>
                        <li>Black list - email domains preventing auto-endorsement.</li>
                    </ul>
                </Typography>
            </AccordionDetails>
        </Accordion>
        <List
            filters={<EmailPatternFilter/>}
            filterDefaultValues={{purpose: 'black'}}
            actions={<EmailPatternListActions/>}
            queryOptions={{ placeholderData: undefined }}
        >
            <Datagrid rowClick={false} bulkActionButtons={<EmailPatternBulkDeleteButton/>}>
                <TextField source="id" label="Domains"/>
            </Datagrid>
        </List>
    </Box>
);

export const EmailPatternCreate = () => {
    const [searchParams] = useSearchParams();
    const defaultPurpose = searchParams.get('purpose') || 'black';

    return (
        <Create>
            <ConsoleTitle>Add Domain</ConsoleTitle>
            <SimpleForm defaultValues={{purpose: defaultPurpose}}>
                <TextInput source="id" label="Domain"/>
                <SelectInput
                    source="purpose"
                    choices={emailPatternPurposeOptions}
                    label="Purpose"
                    optionText={(choice: any) => (
                        <span>{choice.name}{" - "} <span style={{ fontSize: '0.9em' }}>{choice.description}</span></span>
                    )}
                />
            </SimpleForm>
        </Create>
    );
};
