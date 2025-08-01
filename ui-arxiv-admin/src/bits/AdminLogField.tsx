import React, { useState } from 'react';
import {
    Box,
    Collapse,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    ExpandLess as ExpandLessIcon,
    ViewList as ViewListIcon
} from '@mui/icons-material';
import { useRecordContext, FieldProps } from 'react-admin';
import AdminLogList from './AdminLogList';

interface AdminLogFieldProps extends FieldProps {
    paperIdSource?: string;
}

const AdminLogField: React.FC<AdminLogFieldProps> = ({ 
    source,
    paperIdSource = 'paper_id'
}) => {
    const [expanded, setExpanded] = useState(false);
    const record = useRecordContext();

    if (!record) return null;


    // Get paper_id and submission_id from the record
    const paper_id = record[paperIdSource];
    const submission_id = record[source];

    console.log("AdminLogField paper_id: " + JSON.stringify(paper_id));
    console.log("AdminLogField submission_id: " + JSON.stringify(submission_id));

    const handleToggle = () => {
        setExpanded(!expanded);
    };

    return (
        <Box>
            <Tooltip title={expanded ? 'Hide admin logs' : 'Show admin logs'}>
                <IconButton
                    onClick={handleToggle}
                    size="small"
                    sx={{
                        transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s ease',
                    }}
                >
                    {expanded ? <ExpandLessIcon /> : <ViewListIcon />}
                </IconButton>
            </Tooltip>
            <Collapse in={expanded} timeout="auto" unmountOnExit>
                    <AdminLogList
                        paper_id={paper_id}
                        submission_id={submission_id}
                    />
            </Collapse>
        </Box>
    );
};

// Export with the correct naming convention for react-admin fields
export default AdminLogField;