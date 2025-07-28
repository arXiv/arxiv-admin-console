import React, {useEffect, useState} from "react";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import {useNavigate} from "react-router-dom";
import {paths as adminApi} from '../types/admin-api';
import FieldNameCell from "../bits/FieldNameCell";
import PlainTextInput from '../bits/PlainTextInput';
import CategoryInput from "../bits/CategoryInput";
import Tooltip from "@mui/material/Tooltip";
import SourceFlagsInput from '../bits/SourceFlagsInput';
import SourceFormatInput from "../bits/SourceFormatInput";
// import LicenseInput from "../bits/LicenseInput";
import {PrepACMClass, PrepDOI, PrepJoyrnalRef, PrepMSCClass, PrepReportNum} from "../helptexts/Prep";
import LicenseField from "../bits/LicenseField";
import { FormControl, MenuItem, Select, Typography, Box, IconButton } from '@mui/material';
import {
    TextField,
    useRecordContext,
    Edit,
    SimpleForm,
    BooleanInput,
    ReferenceField,
    useDataProvider,
    TopToolbar,
    SaveButton, Identifier,
} from 'react-admin';

import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';

type MetadataT = adminApi['/v1/metadata/document_id/{document_id}']['get']['responses']['200']['content']['application/json'];


interface MetadataVersionSelectorProps {
    metadataVersions: MetadataT[];
    currentVersionId?: Identifier;
    label?: string;
}

const MetadataVersionSelector: React.FC<MetadataVersionSelectorProps> = ({
        metadataVersions,
        currentVersionId,
        label = "Version:"
    }) => {
    const navigate = useNavigate();

    if (!metadataVersions || metadataVersions.length === 0) {
        return null;
    }

    // Sort versions to ensure correct navigation
    const sortedVersions = [...metadataVersions].sort((a, b) => a.version - b.version);

    // Find current version index
    const currentIndex = sortedVersions.findIndex(v => v.id === currentVersionId);

    const handleVersionChange = (event: React.ChangeEvent<{ value: unknown }>) => {
        const metadataId = event.target.value as number;
        if (metadataId && metadataId !== currentVersionId) {
            navigate(`/metadata/${metadataId}/edit`);
        }
    };

    const goToPrevVersion = () => {
        if (currentIndex > 0) {
            const prevVersionId = sortedVersions[currentIndex - 1].id;
            navigate(`/metadata/${prevVersionId}/edit`);
        }
    };

    const goToNextVersion = () => {
        if (currentIndex < sortedVersions.length - 1) {
            const nextVersionId = sortedVersions[currentIndex + 1].id;
            navigate(`/metadata/${nextVersionId}/edit`);
        }
    };

    // Determine if prev/next buttons should be disabled
    const isPrevDisabled = currentIndex <= 0;
    const isNextDisabled = currentIndex >= sortedVersions.length - 1 || currentIndex === -1;

    return (
        <Box display="flex" alignItems="center" gap={1}>
            {/* Navigation buttons on the left */}
            <IconButton
                size="small"
                onClick={goToPrevVersion}
                disabled={isPrevDisabled}
                sx={{ padding: '4px' }}
            >
                <NavigateBeforeIcon />
            </IconButton>

            <IconButton
                size="small"
                onClick={goToNextVersion}
                disabled={isNextDisabled}
                sx={{ padding: '4px' }}
            >
                <NavigateNextIcon />
            </IconButton>

            {/* Label and dropdown */}
            <Typography component="span" variant="body1">
                {label}
            </Typography>

            <FormControl size="small" variant="outlined" sx={{ minWidth: 120 }}>
                <Select
                    value={currentVersionId || ''}
                    onChange={handleVersionChange as any}
                    displayEmpty
                    sx={{
                        '& .MuiSelect-select': {
                            paddingY: '4px',
                            display: 'flex',
                            alignItems: 'center'
                        }
                    }}
                >
                    {sortedVersions.map((metadata) => (
                        <MenuItem key={metadata.id} value={metadata.id}>
                            <Box display="flex" alignItems="center">
                                <Typography>v{metadata.version}</Typography>
                                {metadata.id === currentVersionId && (
                                    <Typography component="span" color="text.secondary" sx={{ ml: 1 }}>
                                        (current)
                                    </Typography>
                                )}
                            </Box>
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
        </Box>
    );
};


const MetadataEditToolbar = () => (
    <TopToolbar sx={{ justifyContent: 'flex-start', ml: 2 }}>
        <SaveButton />
    </TopToolbar>
);

const MetadataEditContents = () => {
    const record = useRecordContext();
    const [openAddOwnerDialog, setOpenAddOwnerDialog] = React.useState(false);
    const navigate = useNavigate();
    const [metadata, setMetadata] = useState<MetadataT | null>(null);
    const dataProvider =  useDataProvider();
    const [metadataVersions, setMetadataVersions] = useState<MetadataT[]>([]);

    useEffect(() => {
        async function getMetadataVersions() {
            if (!record?.document_id)
                return;

            try {
                const reply = await dataProvider.getList<MetadataT>('metadata',
                    {
                        filter: { document_id: record.document_id },
                        pagination: { page: 1, perPage: 1000 },
                        sort: { field: 'id', order: 'DESC' }
                    });
                setMetadataVersions(reply.data);

            }
            catch (error) {
                console.error('Error fetching metadata versions:', error);
            }
            finally {
            }
        }

        getMetadataVersions();
    }, [record?.document_id]);

    const otherVersions = (record?.id ? (
        <MetadataVersionSelector
            metadataVersions={metadataVersions}
            currentVersionId={record?.id}
            label={`${record.id} `}
        />
        ) : null
    );

    return (
        <SimpleForm toolbar={<MetadataEditToolbar />}>
            <Box gap={1} display="flex" flexDirection="column"
                 sx={{
                     width: '100%',
                     '& .MuiBox-root': {
                         width: '100%'
                     }
                 }}
            >

                {/* Paper Details */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Table size="small"
                           sx={{
                               '& .MuiTable-root': {  // Targets all Table components inside
                                   width: '100%'
                               },
                               '& .MuiTableCell-root': {
                                   padding: '4px 6px'
                               },
                               '& .MuiFormControl-root': {
                                   margin: '0px 0px'
                               },
                               '& .MuiInputBase-root': {
                                   padding: '2px 2px'
                               },
                           }}
                    >
                        <TableRow>
                            <FieldNameCell>ID/Version</FieldNameCell>
                            <TableCell>
                                {otherVersions}
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Paper ID</FieldNameCell>
                            <TableCell>
                                <ReferenceField reference={"documents"} source={"document_id"} label={""} link={"show"}>
                                    <TextField source={"paper_id"} />
                                    <Typography sx={{ml: 4}} component={"span"}>
                                        {" ID: "}
                                    </Typography>
                                    <TextField source={"id"}/>

                                </ReferenceField>
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Title</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="title" fontSize={"1.2rem"} />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <FieldNameCell>Authors</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="authors"  />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <FieldNameCell>Categories</FieldNameCell>
                            <TableCell>
                                <CategoryInput source="abs_categories"  />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>License</FieldNameCell>
                            <TableCell>
                                <Typography variant={"body1"} sx={{ml: 1}}>
                                    <LicenseField source="license" />
                                </Typography>
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Comments</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="comments" multiline={true} rows={2} resizable={"vertical"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Abstract</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="abstract" multiline={true} rows={8} resizable={"vertical"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Proxy</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="proxy" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Source Format</FieldNameCell>
                            <TableCell>
                                <SourceFormatInput source="source_format" name={""} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Source Flags</FieldNameCell>
                            <TableCell>
                                <SourceFlagsInput source="source_flags" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Is Withdrawn</FieldNameCell>
                            <TableCell>
                                <BooleanInput label={""} source={"is_withdrawn"} helperText={false} size={"small"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepReportNum} >
                                    <Typography>Report No.</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="report_num" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepMSCClass}>
                                    <Typography>
                                        MSC Class
                                    </Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="msc_class" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepACMClass}>
                                    <Typography>
                                        ACM Class
                                    </Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="acm_class" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepJoyrnalRef} >
                                    <Typography>JournalRef</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="journal_ref" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepDOI} >
                                    <Typography>DOI</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="doi" />
                            </TableCell>
                        </TableRow>

                    </Table>
                </Paper>
            </Box>
        </SimpleForm>
    );
};

export const MetadataEdit = () => (
    <Edit redirect={false}>
        <MetadataEditContents/>
    </Edit>
);

export default MetadataVersionSelector;