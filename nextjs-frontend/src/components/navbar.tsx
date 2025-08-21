import {Button} from "./ui/button"
import Link from "next/link"
export function Navbar() {
    return(
        <div className="grid grid-cols-3 sticky top-0">
            <div></div>
            <div className="flex itemscenter justify-self-center">
                <Button variant="ghost">Home</Button>
                <Button variant="ghost">About Us</Button>
                <Button variant="ghost">Contact</Button>
                <Button asChild variant="ghost">
                    <Link href="/login">Login</Link>
                </Button>
                <Button asChild variant="ghost">
                    <Link href="/register">Register</Link>
                </Button>
            </div>
            <div className="flex itemscenter justify-self-end">
                <Button asChild variant="ghost">
                    <Link href="/login">Login</Link>
                </Button>
                <Button asChild variant="ghost">
                    <Link href="/register">Register</Link>
                </Button>
            </div>
        </div>
    );
}