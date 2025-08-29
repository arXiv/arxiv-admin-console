import {
    List,
    Datagrid,
    TextField,
    EditButton,
    Edit,
    Create,
    SimpleForm,
    ReferenceInput,
    TextInput,
    useRecordContext,
    ReferenceField,
    ArrayInput,
    SimpleFormIterator,
    Button,
    useAuthProvider,
    Identifier,
    Toolbar,
    SaveButton,
    useNotify,
} from 'react-admin';
import ISODateField from "../bits/ISODateFiled";
import Typography from "@mui/material/Typography";
import UserNameField from "../bits/UserNameField";
import {useContext, useState} from "react";
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Box,
    IconButton,
    TextField as MuiTextField,
    Button as MuiButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import EmailIcon from "@mui/icons-material/Email";
import {RuntimeContext} from "../RuntimeContext";

const templateFilters = [
    <TextInput source="id" label="Search" alwaysOn />,
];

export const EmailTemplateList = () => (
    <List filters={templateFilters}>
        <Datagrid rowClick={false}>
            <TextField source="id" />
            <TextField source="short_name" />
            <TextField source="long_name" />
            <TextField source="data" />
            <ISODateField source="update_date" />
            <ReferenceField reference={"users"} source={"updated_by"} >
                <UserNameField />
            </ReferenceField>
            <EditButton />
        </Datagrid>
    </List>
);

const TemplateTitle = () => {
    const record = useRecordContext();
    return <span>Template {record ? `"${record.short_name}"` : ''}</span>;
};


const SendTestEmailDialogImpl = ({ open, onClose, templateId, templateName, record }: {
    open: boolean;
    onClose: () => void;
    templateId: Identifier;
    templateName: string;
    record: any;
}) => {
    const runtimeProps = useContext(RuntimeContext);
    const [formData, setFormData] = useState({
        subject: `Test: ${templateName}`,
        variables: [{ key: '', value: '' }]
    });
    const notify = useNotify();

    const handleSend = async () => {
        // TODO: Implement actual email sending logic
        console.log('Sending test email with data:', {
            templateId,
            subject: formData.subject,
            variables: formData.variables
        });
        const sender = runtimeProps.adminFetcher.path('/v1/email_templates/{id}/send').method('post').create();

        try {
            const respones = await sender({id: Number(templateId), ...formData});
        }
        catch (e: any) {
            notify(`Error sending test email: ${e.message}${e.detail}`, {type: 'error'});
            return;
        }

        onClose();
    };

    const handleAddVariable = () => {
        setFormData(prev => ({
            ...prev,
            variables: [...prev.variables, { key: '', value: '' }]
        }));
    };

    const handleRemoveVariable = (index: number) => {
        setFormData(prev => ({
            ...prev,
            variables: prev.variables.filter((_, i) => i !== index)
        }));
    };

    const handleVariableChange = (index: number, field: 'key' | 'value', value: string) => {
        setFormData(prev => ({
            ...prev,
            variables: prev.variables.map((item, i) => 
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>
                Email Test
                <IconButton
                    onClick={onClose}
                    sx={{ position: 'absolute', right: 8, top: 8 }}
                >
                    <CloseIcon />
                </IconButton>
            </DialogTitle>
            <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                    <MuiTextField
                        label="Subject"
                        value={formData.subject}
                        onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                        fullWidth
                        variant="outlined"
                    />

                    <MuiTextField
                        label="Template Data"
                        value={record?.data || ''}
                        multiline
                        rows={8}
                        fullWidth
                        variant="outlined"
                        InputProps={{
                            readOnly: true,
                        }}
                        sx={{
                            '& .MuiInputBase-input': {
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                            }
                        }}
                    />

                    <Typography variant="h6" sx={{ mt: 2 }}>
                        Template Variables
                    </Typography>
                    
                    {formData.variables.map((variable, index) => (
                        <Box key={index} sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <MuiTextField
                                label="Key"
                                value={variable.key}
                                onChange={(e) => handleVariableChange(index, 'key', e.target.value)}
                                sx={{ flex: 1 }}
                                variant="outlined"
                                size="small"
                            />
                            <MuiTextField
                                label="Value"
                                value={variable.value}
                                onChange={(e) => handleVariableChange(index, 'value', e.target.value)}
                                sx={{ flex: 1 }}
                                variant="outlined"
                                size="small"
                            />
                            <IconButton
                                onClick={() => handleRemoveVariable(index)}
                                disabled={formData.variables.length === 1}
                                size="small"
                            >
                                <CloseIcon />
                            </IconButton>
                        </Box>
                    ))}
                    
                    <MuiButton
                        onClick={handleAddVariable}
                        variant="outlined"
                        sx={{ alignSelf: 'flex-start' }}
                        size="small"
                    >
                        Add Variable
                    </MuiButton>
                </Box>
            </DialogContent>
            <DialogActions>
                <MuiButton onClick={onClose} variant="outlined">
                    Cancel
                </MuiButton>
                <MuiButton onClick={handleSend} variant="contained" startIcon={<EmailIcon />}>
                    Send Test Email
                </MuiButton>
            </DialogActions>
        </Dialog>
    );
};



const SendTestEmailDialog = ({ open, onClose}: {
    open: boolean;
    onClose: () => void;
}) => {
    const record = useRecordContext();
    if (!record) return null;

    return <SendTestEmailDialogImpl open={open} onClose={onClose} templateId={record.id}
                                    templateName={record.short_name || record.id} record={record}/>
}


const EmailTemplateEditToolbar = () => {
    const [dialogOpen, setDialogOpen] = useState(false);

    const handleOpenDialog = () => setDialogOpen(true);
    const handleCloseDialog = () => setDialogOpen(false);

    return (
        <Toolbar>
            <SaveButton />
            <MuiButton
                onClick={handleOpenDialog}
                variant="outlined"
                startIcon={<EmailIcon />}
                sx={{ ml: 1 }}
            >
                Test Email...
            </MuiButton>
            <SendTestEmailDialog
                open={dialogOpen}
                onClose={handleCloseDialog}
            />
        </Toolbar>
    );
};

export const EmailTemplateEdit = () => (
    <Edit title={<TemplateTitle />} actions={false}>
        <SimpleForm toolbar={<EmailTemplateEditToolbar />}>
            <Typography component={"span"} >
                {"ID: "}
                <TextField source="id" />
            </Typography>
            <TextInput source="short_name" />
            <TextInput source="long_name" />
            <TextInput source="data" multiline rows={20} />
        </SimpleForm>
    </Edit>
);

export const EmailTemplateCreate = () => (
    <Create>
        <SimpleForm>
            <TextInput source="short_name" />
            <TextInput source="long_name" />
            <TextInput source="data" multiline rows={20} />
        </SimpleForm>
    </Create>
);
