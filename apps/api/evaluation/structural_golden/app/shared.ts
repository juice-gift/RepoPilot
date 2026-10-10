export interface User { name: string }
export type UserId = string;
export enum State { Ready, Done }
export const formatName = (value: string) => value;
export class Presenter {
  show(value: string) { return formatName(value); }
}
