import { IconButton } from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import { useRecordContext } from 'react-admin';

const EmailLinkField = () => {
    const record = useRecordContext();

    if (!record || !record.email) {
        return null;
    }

    return (
        <IconButton
            component="a"
            href={`mailto:${record.email}`}
            aria-label="Email"
        >
            <EmailIcon />
        </IconButton>
    );
};

export default EmailLinkField;
