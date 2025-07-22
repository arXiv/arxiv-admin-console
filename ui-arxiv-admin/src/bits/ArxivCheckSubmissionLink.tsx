import CheckIcon from '@mui/icons-material/Check';
import {RuntimeContext} from "../RuntimeContext";
import {useContext} from "react";
import UriTemplate from 'uri-templates';
import {useRecordContext} from "react-admin";

const ArxivCheckSubmissionLink = () => {
    const record = useRecordContext();
    const runtimeProps = useContext(RuntimeContext);

    if (!record) return null;

    const url = UriTemplate(runtimeProps.URLS.CheckSubmissionLink).fill({
        arxivCheck: runtimeProps.ARXIV_CHECK,
        submissionId: record.id,
    });

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
        e.preventDefault();
        // Use a named window instead of "_blank" to reuse the tab
        const windowName = "arxiv-check";
        window.open(url, windowName, "noopener,noreferrer");
    };

    return (
        <a href={url} onClick={handleClick}>
            <CheckIcon sx={{width: 16, height: 16}}/>
        </a>
    );
};

export default ArxivCheckSubmissionLink;
