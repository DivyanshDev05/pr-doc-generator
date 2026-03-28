import pytest

from providers import PROVIDERS, get_provider, providers_by_category


class TestGetProvider:
    """Test get_provider function."""

    def test_get_provider_valid_groq(self):
        """Valid provider 'groq' should return correct config."""
        provider = get_provider("groq")
        assert provider["category"] == "free"
        assert "llama-3.3-70b-versatile" in provider["models"]

    def test_get_provider_valid_ollama(self):
        """Valid provider 'ollama' should return correct config."""
        provider = get_provider("ollama")
        assert provider["category"] == "local"
        assert provider["key_env"] is None

    def test_get_provider_valid_anthropic(self):
        """Valid provider 'anthropic' should return correct config."""
        provider = get_provider("anthropic")
        assert provider["category"] == "paid"
        assert "claude-opus-4-5" in provider["models"]

    def test_get_provider_invalid_raises_error(self):
        """Invalid provider should raise ValueError."""
        with pytest.raises(ValueError) as exc:
            get_provider("invalid_provider")
        assert "invalid_provider" in str(exc.value)

    def test_get_provider_lists_available(self):
        """Error message should list available providers."""
        with pytest.raises(ValueError) as exc:
            get_provider("invalid")
        available = str(exc.value)
        assert "groq" in available
        assert "anthropic" in available


class TestProvidersByCategory:
    """Test providers_by_category function."""

    def test_groups_all_providers(self):
        """All providers should be grouped by category."""
        groups = providers_by_category()
        
        assert "paid" in groups
        assert "free" in groups
        assert "local" in groups

    def test_paid_contains_anthropic_openai_gemini(self):
        """Paid category should contain Anthropic, OpenAI, Gemini."""
        groups = providers_by_category()
        paid = groups["paid"]
        
        assert "anthropic" in paid
        assert "openai" in paid
        assert "gemini" in paid

    def test_free_contains_groq_openrouter(self):
        """Free category should contain Groq and OpenRouter."""
        groups = providers_by_category()
        free = groups["free"]
        
        assert "groq" in free
        assert "openrouter" in free

    def test_local_contains_ollama_lmstudio(self):
        """Local category should contain Ollama and LM Studio."""
        groups = providers_by_category()
        local = groups["local"]
        
        assert "ollama" in local
        assert "lmstudio" in local


class TestProviderConfig:
    """Test provider configuration completeness."""

    def test_all_providers_have_required_fields(self):
        """Every provider should have all required fields."""
        required = ["label", "category", "models", "default_model"]
        
        for key, provider in PROVIDERS.items():
            for field in required:
                assert field in provider, f"{key} missing {field}"

    def test_all_providers_have_sdk(self):
        """Every provider should have an sdk defined."""
        for key, provider in PROVIDERS.items():
            assert "sdk" in provider, f"{key} missing sdk"

    def test_all_providers_have_base_url_or_none(self):
        """Every provider should have base_url (or None for custom SDK)."""
        for key, provider in PROVIDERS.items():
            assert "base_url" in provider, f"{key} missing base_url"

    def test_default_model_in_models_list(self):
        """Default model should be in the models list."""
        for key, provider in PROVIDERS.items():
            assert provider["default_model"] in provider["models"], \
                f"{key} default_model not in models list"

    def test_local_providers_have_no_key_env(self):
        """Local providers (ollama, lmstudio) should have no key_env."""
        groups = providers_by_category()
        local = groups["local"]
        
        for key, provider in local.items():
            assert provider["key_env"] is None, f"{key} should not have key_env"

    def test_paid_and_free_providers_have_key_env(self):
        """Paid and free providers should have key_env."""
        groups = providers_by_category()
        
        for category in ["paid", "free"]:
            for key, provider in groups[category].items():
                assert provider["key_env"] is not None, f"{key} should have key_env"
