
export function getRemainingTimeInSeconds(isoTimestamp: string): number
{
    const parsedDate = new Date(isoTimestamp);
    const currentDate = new Date();
    return Math.floor((parsedDate.getTime() - currentDate.getTime()) / 1000);
}
