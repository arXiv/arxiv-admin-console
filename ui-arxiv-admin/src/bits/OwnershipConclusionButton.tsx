import { ButtonProps, useSaveContext } from "react-admin";

import {components} from "../types/admin-api";
type WorkflowStatusType = components["schemas"]["WorkflowStatus"];
import { useFormContext } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';


interface OwnershipConclusionButtonProps extends ButtonProps {
    nextId: number | null,
    setWorkflowStatus: (newStatus: WorkflowStatusType) => void,
    conclusion: WorkflowStatusType,
    buttonLabel: string,
}


const OwnershipConclusionButton = ({ nextId, setWorkflowStatus, conclusion, buttonLabel, disabled, ...props }: OwnershipConclusionButtonProps) => {
    const { save, saving } = useSaveContext();
    const { handleSubmit } = useFormContext();
    const navigate = useNavigate();

    const onSubmit = handleSubmit(async (values) => {
        const updatedValues = { ...values, workflow_status: conclusion };
        setWorkflowStatus(conclusion);
        if (save) {
            await save(updatedValues);
            if (nextId) {
                navigate(`/ownership_requests/${nextId}`);
            }
        }
    });

    return (
        <Button
            data-testid={`ownership-request-${buttonLabel.toLowerCase()}-button`}
            onClick={onSubmit}
            disabled={disabled || saving}
            {...props}
        >
            {buttonLabel}
        </Button>
    );
};

export default OwnershipConclusionButton;
