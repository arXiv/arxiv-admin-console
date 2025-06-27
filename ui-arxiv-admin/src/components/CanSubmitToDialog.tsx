import React, {useEffect, useState} from "react";
import { paths as adminApi } from '../types/admin-api';
import {Identifier, useDataProvider, useRecordContext} from "react-admin";
import CategoryChooserDialog from "./CategoryChooserDialog";
import { CircularProgress, Box, Dialog, DialogTitle, DialogContent } from "@mui/material";

type CanSubmitToT = adminApi['/v1/users/{user_id}/can-submit-to']['get']['responses']['200']['content']['application/json'][0];

const CanSubmitToDialog: React.FC<
    {
        open: boolean;
        setOpen: (open: boolean) => void;
    }
> = ({ open, setOpen }) => {
    const [canSubmitTo, setCanSubmitTo] = useState<Map<string, boolean> >(new Map<string, boolean>());
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const dataProvider = useDataProvider();
    const record = useRecordContext();
    const userId = record?.id as Identifier;

    useEffect(() => {
        if (open && userId) {
            console.log("fetching canSubmitTo for user " + userId);
            setIsLoading(true);

            const fetchCanSubmitTo = async () => {
                try {
                    const { data } = await dataProvider.getList<CanSubmitToT>('can_submit_to', {
                        filter: { user_id: userId },
                        pagination: { page: 1, perPage: 1000 },
                        sort: { field: 'id', order: 'ASC' }
                    });

                    const cats = new Map<string, boolean>();
                    for (const domain of data) {
                        cats.set(domain.archive + "." + domain.subject_class, domain.positive);
                    }
                    setCanSubmitTo(cats);
                } catch (error) {
                    console.error("Error fetching moderation domains:", error);
                } finally {
                    setIsLoading(false);
                }
            };

            fetchCanSubmitTo();
        }
    }, [open, userId, dataProvider]);

    if (!userId) return null;


    return (
        <CategoryChooserDialog
            title="Can submit to"
            open={open}
            setOpen={setOpen}
            currentCategories={canSubmitTo}
            isLoading={isLoading}
        />
    );
};

export default CanSubmitToDialog;