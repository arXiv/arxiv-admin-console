import React, {useEffect, useState} from "react";

import { paths as adminApi } from '../types/admin-api';
import {useDataProvider, useRefresh} from "react-admin";
import CategoryChooserDialog from "./CategoryChooserDialog";

type EndorsementT = adminApi['/v1/endorsements/']['get']['responses']['200']['content']['application/json'][0];
type EndorsementCreateT = adminApi['/v1/endorsements/']['post']['requestBody']['content']['application/json'];


const EndorsementCategoryDialog: React.FC<
    {
        open: boolean;
        setOpen: (open: boolean) => void;
        userId: number;
    }
> = ({ open, setOpen, userId }) => {
    const [endorsementCategories0, setEndorsementCategories0] = useState<Map<string, boolean>>(new Map<string, boolean>());
    const [endorsementCategories, setEndorsementCategories] = useState<Map<string, boolean>>(new Map<string, boolean>());
    const [comment, setComment] = useState<string >("");
    const dataProvider = useDataProvider();
    const refresh = useRefresh();

    useEffect(() => {
        if (open && userId) {
            const fetchEndorsements = async () => {
                try {
                    const { data } = await dataProvider.getList<EndorsementT>('endorsements', {
                        filter: { endorsee_id: userId },
                        pagination: { page: 1, perPage: 1000 },
                        sort: { field: 'id', order: 'ASC' }
                    });

                    const selection = new Map<string, boolean>()
                    for (const endorsement of data) {
                        const category = endorsement.archive + "." + endorsement.subject_class;
                        selection.set(category, true);
                    }

                    setEndorsementCategories0(selection);
                    setEndorsementCategories(selection);
                } catch (error) {
                    console.error("Error fetching endorsements:", error);
                }
            };

            fetchEndorsements();
        }
    }, [open, userId, dataProvider]);


    const handleUpdate = (cat_id: string, _cats: Map<string, boolean>, on_or_off: boolean) => {
        setEndorsementCategories(prevMap => {
            const newMap = new Map(prevMap);
            newMap.set(cat_id, on_or_off);
            return newMap;
        });
    };


    const handleSave = async () => {
        const deleteOperations: string[] = [];
        const createOperations: EndorsementCreateT[] = [];

        for (const [key, value] of endorsementCategories.entries()) {
            const [archive, subject_class] = key.split(".");

            if (!value) {
                const id = `${userId}+${archive}+${subject_class}`;
                deleteOperations.push(id);
            } else if (endorsementCategories0.get(key) !== value) {
                const endorsement: EndorsementCreateT = {
                    endorsee_id: String(userId),
                    endorser_id: "",
                    archive: archive,
                    subject_class: subject_class,
                    type_: "admin",
                    point_value: 10,
                    flag_valid: true,
                    flag_knows_personally: true,
                    flag_seen_paper: false,
                    comment: comment,
                };
                createOperations.push(endorsement);
            }
        }

        if (deleteOperations.length > 0) {
            try {
                await dataProvider.deleteMany('endorsements', { ids: deleteOperations });
            } catch (error) {
                console.error("Error deleting endorsements:", error);
            }
        }

        for (const endorsement of createOperations) {
            try {
                await dataProvider.create('endorsements', { data: endorsement },);
            } catch (error) {
                console.error("Error creating moderator:", error);
            }
        }

        refresh();
    };


    if (!endorsementCategories) return null;

    return (
        <CategoryChooserDialog
            title="Endorsement Categories"
            open={open}
            setOpen={setOpen}
            currentCategories={endorsementCategories}
            onUpdateCategory={handleUpdate}
            onSaveUpdates={handleSave}
            comment={comment}
            setComment={setComment}
        />

    );
};

export default EndorsementCategoryDialog;
