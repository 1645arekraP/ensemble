import { cn } from "@/lib/utils";
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"

import { Label } from "@/components/ui/label"
import { useState } from 'react';
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

const formSchema = z.object({
  email: z.email({
    message: "Please enter a valid email address.",
  }),
  password: z.string().min(8, {
    message: "Password must be at least 8 characters long.",
  }),
  passwordConfirmation: z.string().min(8, {
    message: "Password must be at least 8 characters long.",
  }),
}).refine((data) => data.password === data.passwordConfirmation, {
  message: "Passwords do not match.",
  path: ["passwordConfirmation"],
});
 
 
 
 
 export function RegisterForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
    const [submissionMessage, setSubmissionMessage] = useState({status: '', text: ''});
    const router = useRouter();
    const { login } = useAuth();
    const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
        email: "",
        password: "",
        passwordConfirmation: "",
    },
    });


  async function onSubmit(values: z.infer<typeof formSchema>) {
    const backendUrl = "http://127.0.0.1:8000/api/auth/signup/";

    // Payload for the request.
    const payload = {
      email: values.email,
      password: values.password,
    };

    try {
      const response = await fetch(backendUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        console.log("Registration successful!", data);
        setSubmissionMessage({
          status: "success",
          text: "Sign Up Successful! Redirecting to login...",
        });
        
        // TODO: Maybe make it more secure
        login(data.access_token, data.refresh_token);
        
      } else {
        console.error("Registration failed:", data);
        const errorText = data.email ? data.email[0] : (data.detail || 'An error occurred.');
        setSubmissionMessage({
          status: "error",
          text: `Registration failed: ${errorText}`,
        });
      }
    } catch (error) {
      console.error("Network error:", error);
      setSubmissionMessage({
        status: "error",
        text: "A network error occurred. Please check your connection.",
      });
    }

    form.reset();
  };
  
  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="p-6 py-8">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
          {/*
          <CardDescription>
            Enter your email below to create your account
          </CardDescription>
          */}
        </CardHeader>
        <CardContent>
          <Form {...form}>

            <form onSubmit={form.handleSubmit(onSubmit)}>
                <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="your@email.com"
                        className="rounded-lg"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              </div>
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem className="grid gap-3">
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="********"
                        className="rounded-lg"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="passwordConfirmation"
                render={({ field }) => (
                  <FormItem className="grid gap-3">
                    
                      <FormLabel>Password</FormLabel>
                      
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="********"
                        className="rounded-lg"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex flex-col gap-3">
                <Button type="submit" className="w-full hover:cursor-pointer">
                  Register
                </Button>
              </div>
            </div>
                <div className="mt-4 text-center text-sm">
                    Already have an account?{" "}
                    <a href="/login" className="underline underline-offset-4">
                        Login
                    </a>
                </div>
            </form>
        </Form>
        </CardContent>
      </Card>
    </div>
  )
}