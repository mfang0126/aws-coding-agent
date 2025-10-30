"""
Setup OAuth2 credential provider for GitHub authentication.
Based on bedrock-agent-template pattern.
Run this once before deploying the agent.
"""
import sys
import time

import boto3

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


def create_github_oauth_provider() -> str:
    """
    Create OAuth2 credential provider for GitHub in AgentCore Identity.
    This enables 3-Legged OAuth (USER_FEDERATION) for per-user tokens.

    Returns:
        Provider ARN

    Raises:
        Exception: If provider creation fails
    """
    client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

    # Delete existing provider if it exists (for updates)
    try:
        providers = client.list_oauth2_credential_providers()
        existing = [
            p for p in providers.get('credentialProviders', [])
            if p['name'] == settings.github_provider_name
        ]
        if existing:
            logger.info("♻️  Deleting existing provider...")
            client.delete_oauth2_credential_provider(
                name=settings.github_provider_name
            )
            time.sleep(5)  # Wait for cleanup
    except Exception as e:
        logger.info("no_existing_provider", error=str(e))

    # Create new provider
    logger.info("creating_oauth_provider", name=settings.github_provider_name)
    response = client.create_oauth2_credential_provider(
        name=settings.github_provider_name,
        credentialProviderVendor='GithubOauth2',
        oauth2ProviderConfigInput={
            'githubOauth2ProviderConfig': {
                'clientId': settings.github_client_id.get_secret_value(),
                'clientSecret': settings.github_client_secret.get_secret_value()
            }
        }
    )

    provider_arn = response['credentialProviderArn']
    callback_url = response.get('callbackUrl', 'N/A')

    print("\n" + "="*60)
    print(f"✅ Created OAuth provider: {provider_arn}")
    print(f"   Provider name: {settings.github_provider_name}")
    print(f"   Vendor: GithubOauth2")
    print("\n" + "="*60)
    print("🔗 IMPORTANT: Register this callback URL in your GitHub OAuth App:")
    print(f"   {callback_url}")
    print("\n📝 Steps to register:")
    print("   1. Go to https://github.com/settings/developers")
    print("   2. Select your OAuth App")
    print("   3. Add the callback URL above to 'Authorization callback URL'")
    print("   4. Save changes")
    print("="*60 + "\n")

    logger.info(
        "oauth_provider_created",
        provider_arn=provider_arn,
        callback_url=callback_url
    )

    return provider_arn


def verify_provider_setup() -> bool:
    """
    Verify the provider was created correctly.

    Returns:
        True if provider exists, False otherwise
    """
    client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

    providers = client.list_oauth2_credential_providers()
    github_provider = next(
        (p for p in providers.get('credentialProviders', [])
         if p['name'] == settings.github_provider_name),
        None
    )

    if github_provider:
        print("✅ Provider verified:")
        print(f"   ARN: {github_provider['credentialProviderArn']}")
        print(f"   Name: {github_provider['name']}")
        logger.info("provider_verified", provider=github_provider)
        return True
    else:
        print("❌ Provider not found!")
        logger.error("provider_not_found", name=settings.github_provider_name)
        return False


def main():
    """Main entrypoint for setup script."""
    from ..utils.logging import setup_logging
    setup_logging(settings.log_level)

    logger.info("🔐 Setting up GitHub OAuth provider...")

    try:
        provider_arn = create_github_oauth_provider()
        logger.info("provider_created", arn=provider_arn)

        # Verify setup
        if verify_provider_setup():
            logger.info("✅ Setup complete!")
            sys.exit(0)
        else:
            logger.error("❌ Verification failed")
            sys.exit(1)

    except Exception as e:
        logger.error("setup_failed", error=str(e), exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
