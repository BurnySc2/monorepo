import React from "react"
import Document, { Html, Head, Main, NextScript } from "next/document"

class MyDocument extends Document {
    static async getInitialProps(ctx) {
        const initialProps = await Document.getInitialProps(ctx)
        return { ...initialProps }
    }

    render() {
        return (
            <Html>
                <Head>
                    <link
                        rel="stylesheet"
                        href="https://cdnjs.cloudflare.com/ajax/libs/basscss/8.1.0/css/basscss.min.css"
                        integrity="sha512-09PehPv7gV9Sw80QKw0/AJ/wBtQFfIAUNz+LbxMiLnT0OeTHCw4DOQKwPP7ztmLKd4vpONSGD32pnFXZW2weKw=="
                        crossOrigin="anonymous"
                    />
                </Head>
                <body>
                    <Main />
                    <NextScript />
                </body>
            </Html>
        )
    }
}

export default MyDocument
