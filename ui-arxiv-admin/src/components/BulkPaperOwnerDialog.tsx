import React, { useContext, useEffect, useState } from 'react';
import {
    useDataProvider,
    useNotify,
    useRefresh,
    Datagrid,
    TextField,
    RecordContextProvider,
    ListContextProvider,
    Pagination
} from 'react-admin';
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Typography from "@mui/material/Typography";
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import MuiTextField from "@mui/material/TextField";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import UploadIcon from '@mui/icons-material/Upload';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { styled } from '@mui/material/styles';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';

import { RuntimeContext } from "../RuntimeContext";
import { paths as adminApi } from '../types/admin-api';
import { useRecordContext } from 'react-admin';
import HighlightText from '../bits/HighlightText';
import UserNameField from "../bits/UserNameField";

type PaperOwnershipUpdateRequest = adminApi['/v1/paper_owners/user/{user_id}']['post']['responses']['200']['content']['application/json'];

const VisuallyHiddenInput = styled('input')({
    clip: 'rect(0 0 0 0)',
    clipPath: 'inset(50%)',
    height: 1,
    overflow: 'hidden',
    position: 'absolute',
    bottom: 0,
    left: 0,
    whiteSpace: 'nowrap',
    width: 1,
});

interface BulkPaperOwnerDialogProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    userId: number;
    userRecord: any;
}

// Custom field component for highlighting authors
const AuthorsField: React.FC<{ userName: string[] }> = ({ userName }) => {
    const record = useRecordContext();
    
    if (!record?.authors || !userName) {
        return <TextField source="authors" />;
    }

    return (
        <HighlightText 
            text={record.authors}
            highlighters={userName}
        />
    );
};


// Custom Datagrid with pagination support using manual list context
const DocumentDatagrid: React.FC<{ 
    documents: any[]; 
    totalDocuments: number; 
    userName: string[];
}> = ({ 
    documents, 
    totalDocuments, 
    userName
}) => {
    const [page, setPage] = useState(1);
    const [perPage, setPerPage] = useState(5);
    
    const startIndex = (page - 1) * perPage;
    const paginatedData = documents.slice(startIndex, startIndex + perPage);
    
    // Create manual list context
    const listContextValue = {
        data: paginatedData,
        total: totalDocuments,
        page,
        perPage,
        setPage,
        setPerPage,
        resource: 'bulk-documents',
        isLoading: false,
        isPending: false,
        error: null,
        hasNextPage: startIndex + perPage < totalDocuments,
        hasPreviousPage: page > 1,
        sort: { field: 'id', order: 'ASC' },
        setSort: () => {},
        filterValues: {},
        setFilters: () => {},
        displayedFilters: {},
        showFilter: () => {},
        hideFilter: () => {},
        selectedIds: [],
        onSelect: () => {},
        onSelectAll: () => {},
        onToggleItem: () => {},
        onUnselectItems: () => {},
        refetch: () => Promise.resolve(),
        isFetching: false,
        defaultTitle: 'Documents',
        // Additional properties that might be missing
        loaded: true,
        loading: false,
        onSelectAllInPage: () => {},
        onUnselectAll: () => {},
        onSelectAllInFilter: () => {},
        ids: paginatedData.map(item => item.id || item.paper_id),
        meta: undefined,
        storeKey: false
    } satisfies Partial<any>;

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <ListContextProvider value={listContextValue as any}>
                <Box sx={{ 
                    flexGrow: 1, 
                    overflow: 'auto', 
                    maxHeight: '420px',
                    '& .RaDatagrid-table': {
                        overflow: 'auto'
                    }
                }}>
                    <Datagrid bulkActionButtons={false} rowClick={false}>
                        <TextField source="paper_id" label="Paper ID" />
                        <TextField source="title" label="Title" />
                        <AuthorsField userName={userName} />
                    </Datagrid>
                </Box>
                <Box sx={{ mt: 1, flexShrink: 0 }}>
                    <Pagination />
                </Box>
            </ListContextProvider>
        </Box>
    );
};

const steps = ['Upload Paper IDs', 'Confirm Ownership'];

const BulkPaperOwnerDialog: React.FC<BulkPaperOwnerDialogProps> = ({ open, setOpen, userId, userRecord }) => {
    const [paperIds, setPaperIds] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [activeStep, setActiveStep] = useState(0);
    const [ownershipRequest, setOwnershipRequest] = useState<PaperOwnershipUpdateRequest | null>(null);
    const [documents, setDocuments] = useState<any[]>([]);
    const [totalDocuments, setTotalDocuments] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [userName, setUserName] = useState<string[]>([]);
    const [authorshipSelection, setAuthorshipSelection] = useState<'unselected' | 'authored' | 'not_authored'>('unselected');
    
    const runtimeProps = useContext(RuntimeContext);
    const dataProvider = useDataProvider();
    const notify = useNotify();
    const refresh = useRefresh();

    // Get user's name for highlighting
    useEffect(() => {
        if (userRecord && open) {
            setUserName([userRecord.first_name,  userRecord.last_name]);
        }
    }, [userRecord, open]);

    const handleClose = () => {
        setOpen(false);
        setActiveStep(0);
        setPaperIds('');
        setSelectedFile(null);
        setOwnershipRequest(null);
        setDocuments([]);
        setTotalDocuments(0);
        setAuthorshipSelection('unselected');
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            // Read file content and set it to paperIds for preview
            const reader = new FileReader();
            reader.onload = (e) => {
                const content = e.target?.result as string;
                setPaperIds(content);
            };
            reader.readAsText(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile && !paperIds.trim()) {
            notify('Please select a file or enter paper IDs', { type: 'warning' });
            return;
        }

        setIsLoading(true);
        try {
            const formData = new FormData();
            if (selectedFile) {
                formData.append('file', selectedFile);
            } else {
                formData.append('content', paperIds);
            }
            formData.append('file_format', 'csv');

            const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/v1/paper_owners/user/${userId}`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(errorData.detail || 'Request failed');
            }

            const data = await response.json();
            setOwnershipRequest(data);

            // Fetch document details
            const documentIds = data.authored.map((id: string) => {
                const match = id.match(/user_\d+-doc_(\d+)/);
                return match ? parseInt(match[1]) : null;
            }).filter(Boolean);

            if (documentIds.length > 0) {
                try {
                    const docsResponse = await dataProvider.getMany('documents', { ids: documentIds });
                    setDocuments(docsResponse.data);
                    setTotalDocuments(docsResponse.data.length);
                } catch (error) {
                    console.error('Error fetching documents:', error);
                    setTotalDocuments(data.authored.length);
                    setDocuments([]);
                    setAuthorshipSelection('unselected');
                }
            }

            setActiveStep(1);
        } catch (error: any) {
            notify(`Failed to process paper IDs: ${error?.detail || error.message}`, { type: 'error' });
        } finally {
            setIsLoading(false);
        }
    };


    const handleConfirm = async () => {
        if (!ownershipRequest) return;

        setIsLoading(true);
        try {
            // Build the updated ownership request based on global authorship selection
            const updatedRequest: PaperOwnershipUpdateRequest = {
                authored: [],
                not_authored: [],
                valid: ownershipRequest.valid,
                auto: ownershipRequest.auto,
                timestamp: ownershipRequest.timestamp
            };

            // Apply the global selection to all papers
            if (authorshipSelection === 'authored') {
                updatedRequest.authored = [...ownershipRequest.authored];
            } else if (authorshipSelection === 'not_authored') {
                updatedRequest.not_authored = [...ownershipRequest.authored];
            }
            // 'unselected' leaves both arrays empty

            await dataProvider.update('paper_owners/authorship', {
                id: 'upsert',
                data: updatedRequest,
                previousData: {}
            });
            
            notify('Paper owners updated successfully', { type: 'success' });
            handleClose();
            refresh();
        } catch (error: any) {
            notify(`Failed to update paper owners: ${error?.detail || error.message}`, { type: 'error' });
        } finally {
            setIsLoading(false);
        }
    };


    return (
        <Dialog open={open} onClose={handleClose} maxWidth="xl" fullWidth>
            <DialogTitle>
                Bulk Paper Owner Assignment
            </DialogTitle>
            
            <Box sx={{ px: 3, pt: 1, minWidth: 400 }}>
                <Stepper activeStep={activeStep} alternativeLabel>
                    {steps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>
            </Box>
            
            <DialogContent sx={{ display: 'flex', justifyContent: activeStep === 0 ? 'center' : 'stretch' }}>
                {activeStep === 0 ? (
                    <Box sx={{ minWidth: 400, maxWidth: 600 }} alignItems={'center'}>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                            Upload a file or enter paper IDs (one per line):
                        </Typography>
                        <Box sx={{ mb: 2 }}>
                            <Button
                                component="label"
                                variant="outlined"
                                startIcon={<CloudUploadIcon />}
                                disabled={isLoading}
                            >
                                Choose File
                                <VisuallyHiddenInput type="file" accept=".txt,.csv" onChange={handleFileChange} />
                            </Button>
                            {selectedFile && (
                                <Chip 
                                    label={selectedFile.name}
                                    onDelete={() => {
                                        setSelectedFile(null);
                                        setPaperIds('');
                                    }}
                                    sx={{ ml: 2 }}
                                />
                            )}
                        </Box>
                        <MuiTextField
                            fullWidth
                            multiline
                            rows={8}
                            value={paperIds}
                            onChange={(e) => setPaperIds(e.target.value)}
                            placeholder="2401.12345&#10;math-ph/0123456&#10;1234.5678"
                            disabled={isLoading}
                            helperText={selectedFile ? "File content preview (you can edit if needed)" : "Enter paper IDs manually or choose a file above"}
                        />
                    </Box>
                ) : (
                    <Box sx={{ width: '100%' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6" color="textSecondary">
                                <RecordContextProvider value={userRecord}>
                                    {"Review papers to be assigned to "}
                                    <UserNameField withEmail/>
                                </RecordContextProvider>
                            </Typography>
                            <FormControl  sx={{ minWidth: 200, maxWidth: 200, mr: 2 }}>
                                <InputLabel>Authorship</InputLabel>
                                <Select
                                    value={authorshipSelection}
                                    label="Authorship"
                                    onChange={(e) => setAuthorshipSelection(e.target.value as 'unselected' | 'authored' | 'not_authored')}
                                >
                                    <MenuItem value="unselected">Unselected</MenuItem>
                                    <MenuItem value="authored">Authored</MenuItem>
                                    <MenuItem value="not_authored">Not Authored</MenuItem>
                                </Select>
                            </FormControl>
                        </Box>
                        <Box sx={{ width: '100%', height: '500px', overflow: 'hidden' }}>
                            <DocumentDatagrid 
                                documents={documents} 
                                totalDocuments={totalDocuments}
                                userName={userName}
                            />
                        </Box>
                    </Box>
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={handleClose} disabled={isLoading}>
                    Cancel
                </Button>
                {activeStep === 1 && (
                    <Button onClick={() => setActiveStep(0)} disabled={isLoading}>
                        Back
                    </Button>
                )}
                {activeStep === 0 ? (
                    <Button 
                        onClick={handleUpload} 
                        variant="contained" 
                        disabled={isLoading || (!selectedFile && !paperIds.trim())}
                        startIcon={isLoading ? <CircularProgress size={20} /> : <UploadIcon />}
                    >
                        {selectedFile ? `Process File (${selectedFile.name})` : 'Process Papers'}
                    </Button>
                ) : (
                    <Button 
                        onClick={handleConfirm} 
                        variant="contained" 
                        disabled={isLoading || authorshipSelection === 'unselected'}
                        startIcon={isLoading ? <CircularProgress size={20} /> : null}
                    >
                        Confirm Ownership
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default BulkPaperOwnerDialog;