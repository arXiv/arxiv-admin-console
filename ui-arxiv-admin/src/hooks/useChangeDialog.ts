import { useState, useEffect, useRef } from 'react';
import { useDataProvider, useNotify, useRecordContext, Identifier } from 'react-admin';

export interface UseChangeDialogOptions<T> {
    /** Whether the dialog is open */
    open: boolean;
    /** Initial values for the form fields */
    getInitialValues?: (record: any) => T;
    /** Validation function that returns error message or null if valid */
    validate?: (values: T) => string | null;
    /** Data provider resource name (e.g., 'aaa_user_email', 'aaa_user_name') */
    resource: string;
    /** Transform form values into the API payload */
    transformPayload?: (values: T, record: any) => any;
    /** Success message or function to generate success message */
    successMessage?: string | ((values: T, record: any) => string);
    /** Callback after successful update */
    onSuccess?: (values: T) => void;
}

export interface UseChangeDialogReturn<T> {
    /** Form values */
    values: T;
    /** Update a specific field value */
    setValue: <K extends keyof T>(field: K, value: T[K]) => void;
    /** Update all form values */
    setValues: (values: T) => void;
    /** Whether the form is submitting */
    isLoading: boolean;
    /** Current error message, if any */
    error: string | null;
    /** Set error message */
    setError: (error: string | null) => void;
    /** Current user record from context */
    record: any;
    /** Current user ID */
    userId: Identifier | null;
    /** Handle form submission */
    handleSubmit: (event: React.FormEvent) => Promise<void>;
    /** Handle dialog close */
    handleClose: () => void;
    /** Data provider instance */
    dataProvider: any;
    /** Notify instance */
    notify: any;
}

/**
 * Custom hook for managing change dialogs (email, name, password, etc.)
 * Provides common functionality for form state, validation, submission, and error handling.
 */
export function useChangeDialog<T extends Record<string, any>>(
    options: UseChangeDialogOptions<T>
): UseChangeDialogReturn<T> {
    const {
        open,
        getInitialValues,
        validate,
        resource,
        transformPayload,
        successMessage = 'Successfully updated',
        onSuccess,
    } = options;

    const [values, setValues] = useState<T>({} as T);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const dataProvider = useDataProvider();
    const notify = useNotify();
    const record = useRecordContext();

    const userId = record?.id as Identifier | null;
    const prevOpenRef = useRef(open);
    const getInitialValuesRef = useRef(getInitialValues);

    // Keep ref updated
    useEffect(() => {
        getInitialValuesRef.current = getInitialValues;
    }, [getInitialValues]);

    // Initialize and reset form values only when dialog opens (not on every render)
    useEffect(() => {
        // Only reset when dialog transitions from closed to open
        const isOpening = open && !prevOpenRef.current;

        if (isOpening && record && getInitialValuesRef.current) {
            setValues(getInitialValuesRef.current(record));
            setError(null);
        }

        prevOpenRef.current = open;
    }, [open, record]);

    const setValue = <K extends keyof T>(field: K, value: T[K]) => {
        setValues((prev) => ({ ...prev, [field]: value }));
    };

    const handleClose = () => {
        if (!isLoading) {
            // Dialog close is controlled by parent component
            // This is just a safety check
        }
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        // Run validation if provided
        if (validate) {
            const validationError = validate(values);
            if (validationError) {
                setError(validationError);
                return;
            }
        }

        setIsLoading(true);
        setError(null);

        try {
            // Transform values into API payload
            const payload = transformPayload ? transformPayload(values, record) : values;

            // Call the data provider
            await dataProvider.update(resource, {
                id: userId,
                data: payload,
                previousData: record,
            });

            // Show success notification
            const message =
                typeof successMessage === 'function'
                    ? successMessage(values, record)
                    : successMessage;
            notify(message, { type: 'success' });

            // Call success callback
            if (onSuccess) {
                onSuccess(values);
            }

            // Parent component should close the dialog via setOpen(false)
        } catch (err: any) {
            console.error(`Error updating ${resource}:`, JSON.stringify(err));
            // handleHttpError in dataProvider already extracts detail into the message
            // Priority: err.message (which contains the detail) > err.body.detail > fallback
            let message = err?.message || err?.body?.detail || 'An error occurred while updating';
            setError(message);
        } finally {
            setIsLoading(false);
        }
    };

    return {
        values,
        setValue,
        setValues,
        isLoading,
        error,
        setError,
        record,
        userId,
        handleSubmit,
        handleClose,
        dataProvider,
        notify,
    };
}
