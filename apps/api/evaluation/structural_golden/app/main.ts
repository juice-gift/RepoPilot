import { formatName as format, User } from "./shared";
import * as shared from "./shared";

export const show = (user: User) => format(user.name);
show({ name: "demo" });
shared.formatName("demo");
missing();
